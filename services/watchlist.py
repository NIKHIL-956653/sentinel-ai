"""
Watchlist: saved queries re-run on a schedule; new HIGH-confidence stories → Telegram.

Storage (Mongo `watchlist`): {query, query_norm, created_at, last_run, last_new, seen_keys: [..]}
A story's key is its normalised headline, so the same story seen twice is not re-alerted.

Scheduler: a daemon thread started from FastAPI's startup event, every WATCHLIST_INTERVAL_MINUTES.
Honest limitation: on a free PaaS instance that sleeps when idle, the thread sleeps too — use
POST /api/v1/watchlist/run from an external cron (e.g. cron-job.org) to guarantee cadence.
"""
import re
import threading
import time
from datetime import datetime

from config import (WATCHLIST_ENABLED, WATCHLIST_INTERVAL_MINUTES, PUBLIC_SITE_URL, MAX_WATCHES,
                    MAX_QUERY_LENGTH, ALERT_ON_DISPUTED, ALERT_SURGE_FACTOR)
from database import db, _safe, _strip_id
from tools import telegram

watchlist_collection = db["watchlist"]
_lock = threading.Lock()
_thread = None


def story_key(story: dict) -> str:
    title = (story.get("titles") or [""])[0]
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()[:160]


def new_high_confidence(stories: list, seen: set) -> list:
    """Stories with HIGH confidence whose key has not been alerted before."""
    return [s for s in stories
            if (s.get("confidence") or "").upper() == "HIGH" and story_key(s) not in seen]


def new_disputed_claims(stories: list, seen_disputed: set) -> list:
    """[(story, claim_text)] for claims that became disputed and were not alerted before."""
    out = []
    for s in stories:
        for c in s.get("claims") or []:
            if c.get("status") == "disputed":
                key = f"{story_key(s)}|{(c.get('text') or '').strip().lower()[:120]}"
                if key not in seen_disputed:
                    out.append((s, c.get("text", ""), key))
    return out


def surge(prev_count, now_count: int, factor: float = ALERT_SURGE_FACTOR) -> bool:
    """A watched topic 'surges' when its story count jumps by `factor` between runs (min 3 stories)."""
    if not factor or prev_count is None:
        return False
    return now_count >= 3 and now_count >= prev_count * factor and now_count > prev_count


# ── CRUD ────────────────────────────────────────────────────────────────────
def list_watches() -> list:
    docs = _safe(lambda: list(watchlist_collection.find().sort("created_at", -1)), [], "watchlist.list")
    out = []
    for d in docs:
        d = _strip_id(d)
        d["seen_count"] = len(d.pop("seen_keys", []) or [])
        d["disputed_count"] = len(d.pop("seen_disputed", []) or [])
        out.append(d)
    return out


def add_watch(query: str) -> dict:
    q = query.strip()
    if not q:
        raise ValueError("empty query")
    if len(q) > MAX_QUERY_LENGTH:
        raise ValueError(f"query longer than {MAX_QUERY_LENGTH} characters")
    norm = q.lower()
    existing = _safe(lambda: watchlist_collection.find_one({"query_norm": norm}), None, "watchlist.find")
    if existing:
        return {"status": "exists", "query": existing["query"]}
    count = _safe(lambda: watchlist_collection.count_documents({}), 0, "watchlist.count")
    if count >= MAX_WATCHES:
        raise ValueError(f"watchlist is full ({MAX_WATCHES}) — each watch costs a search + LLM calls per interval; remove one first")
    doc = {"query": q, "query_norm": norm, "created_at": datetime.utcnow(),
           "last_run": None, "last_new": 0, "seen_keys": [], "seen_disputed": [], "last_count": None}
    ok = _safe(lambda: watchlist_collection.insert_one(doc), None, "watchlist.insert")
    return {"status": "added" if ok else "not_saved (MongoDB unavailable)", "query": q}


def remove_watch(query: str) -> bool:
    res = _safe(lambda: watchlist_collection.delete_one({"query_norm": query.strip().lower()}), None, "watchlist.delete")
    return bool(res and res.deleted_count)


# ── run ─────────────────────────────────────────────────────────────────────
def run_once(send=telegram.send_message, runner=None) -> dict:
    """Run every watch; alert on new HIGH stories. `send`/`runner` are injectable for tests."""
    from services.news_service import run_news_query, NoArticles
    runner = runner or run_news_query
    if not _lock.acquire(blocking=False):
        return {"status": "already_running"}
    try:
        report = {"status": "ok", "watches": 0, "alerts": 0, "errors": []}
        for w in _safe(lambda: list(watchlist_collection.find()), [], "watchlist.run.list"):
            report["watches"] += 1
            try:
                result = runner(w["query"])
            except NoArticles:
                result = {"results": []}
            except Exception as e:  # one bad query must not stop the others
                report["errors"].append(f"{w['query']}: {e.__class__.__name__}")
                continue
            stories = result.get("results", [])
            seen = set(w.get("seen_keys") or [])
            fresh = new_high_confidence(stories, seen)
            if fresh:
                if send(telegram.format_alert(w["query"], fresh, PUBLIC_SITE_URL)):
                    report["alerts"] += 1
            # rule 2: a claim became disputed
            seen_disputed = set(w.get("seen_disputed") or [])
            disputed = new_disputed_claims(stories, seen_disputed) if ALERT_ON_DISPUTED else []
            if disputed:
                if send(telegram.format_disputed_alert(w["query"], disputed, PUBLIC_SITE_URL)):
                    report["alerts"] += 1
            # rule 3: story-count surge since the previous run
            if surge(w.get("last_count"), len(stories)):
                if send(telegram.format_surge_alert(w["query"], w.get("last_count"), len(stories), PUBLIC_SITE_URL)):
                    report["alerts"] += 1
            keys = list(seen | {story_key(s) for s in fresh})[-500:]
            dkeys = list(seen_disputed | {k for _, _, k in disputed})[-500:]
            _safe(lambda: watchlist_collection.update_one(
                {"_id": w["_id"]},
                {"$set": {"last_run": datetime.utcnow(), "last_new": len(fresh), "seen_keys": keys,
                          "seen_disputed": dkeys, "last_count": len(stories)}}),
                None, "watchlist.update")
        return report
    finally:
        _lock.release()


def _loop():
    print(f"⏰ watchlist scheduler: every {WATCHLIST_INTERVAL_MINUTES} min")
    while True:
        time.sleep(WATCHLIST_INTERVAL_MINUTES * 60)
        try:
            rep = run_once()
            print(f"⏰ watchlist run: {rep}")
        except Exception as e:
            print(f"⏰ watchlist run crashed: {e}")


def start_scheduler() -> bool:
    global _thread
    if not WATCHLIST_ENABLED or _thread is not None:
        return False
    _thread = threading.Thread(target=_loop, name="watchlist", daemon=True)
    _thread.start()
    return True
