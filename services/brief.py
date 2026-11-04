"""
Daily Intelligence Brief (SITREP).

Summarises the last BRIEF_WINDOW_HOURS of archived searches — stories, contradictions, claims,
geotagged regions, cached leader statements — into a structured brief with one LLM call.
Spends nothing new on Tavily: it only reads what the watchlist / users already collected
(leader statements are read from cache only; never fetched here).

Cached in Mongo `briefs` for BRIEF_CACHE_HOURS. A scheduler thread pushes it to Telegram every
BRIEF_INTERVAL_HOURS when a bot is configured. `build_brief(..., llm=)` is injectable for tests.
"""
import html
import threading
import time
from collections import Counter
from datetime import datetime

from config import BRIEF_CACHE_HOURS, BRIEF_INTERVAL_HOURS, BRIEF_WINDOW_HOURS, PUBLIC_SITE_URL, OPENROUTER_MODEL
from database import get_all_stories, get_cached_statements, get_cached_brief, save_brief
from tools.llm import chat_json, LLMError
from tools import telegram

SECTIONS = ["top_developments", "contradictions", "leader_statements", "watch_items"]


def _dedupe(stories: list) -> list:
    seen, out = set(), []
    for s in stories:
        key = ((s.get("titles") or [""])[0]).strip().lower()
        if key and key not in seen:
            seen.add(key)
            out.append(s)
    return out


def gather_inputs(hours: int = BRIEF_WINDOW_HOURS) -> dict:
    """Everything the brief is built from — deterministic, no LLM."""
    stories = _dedupe(get_all_stories(hours))
    stories.sort(key=lambda s: ({"HIGH": 0, "MEDIUM": 1}.get((s.get("confidence") or "").upper(), 2)))
    contradictions, seen_c = [], set()
    # contradictions live on the search doc; get_all_stories flattens results, so re-read them
    from database import get_recent_news
    for search in get_recent_news(hours):
        for c in search.get("contradictions") or []:
            k = (c.get("story1"), c.get("story2"))
            if k not in seen_c:
                seen_c.add(k)
                contradictions.append({**c, "query": search.get("query")})
    disputed_claims = [{"story": (s.get("titles") or [""])[0], "claim": c["text"]}
                       for s in stories for c in (s.get("claims") or []) if c.get("status") == "disputed"]
    regions = Counter(s["geo"]["country"] for s in stories if s.get("geo") and s["geo"].get("country"))
    queries = Counter(s.get("query") for s in stories if s.get("query"))
    statements = get_cached_statements(hours=max(hours, 24)) or []
    return {
        "window_hours": hours,
        "stories": stories,
        "contradictions": contradictions,
        "disputed_claims": disputed_claims,
        "regions": regions.most_common(8),
        "queries": [q for q, _ in queries.most_common(10)],
        "statements": statements[:10],
        "counts": {
            "stories": len(stories),
            "high": sum(1 for s in stories if (s.get("confidence") or "").upper() == "HIGH"),
            "verified": sum(1 for s in stories if (s.get("verdict") or "").startswith("VERIFIED")),
            "disputed": sum(1 for s in stories if (s.get("verdict") or "").startswith("DISPUTED")),
            "contradictions": len(contradictions),
            "sources": len({src for s in stories for src in (s.get("sources") or [])}),
        },
    }


def _prompt(inp: dict) -> str:
    lines = []
    for i, s in enumerate(inp["stories"][:40]):
        geo = s.get("geo", {}).get("country") if s.get("geo") else ""
        lines.append(f"[{i}] ({(s.get('confidence') or '?').upper()}, {s.get('verdict', '')}, {geo or 'global'}) "
                     f"{(s.get('titles') or [''])[0]} — sources: {', '.join((s.get('sources') or [])[:3])}")
    contra = [f"- {c.get('conflict')}: “{c.get('story1')}” vs “{c.get('story2')}”" for c in inp["contradictions"][:10]]
    stmts = [f"- {st.get('leader')} ({st.get('sentiment')}): “{(st.get('statement') or '')[:160]}”" for st in inp["statements"]]
    return f"""You are writing a neutral, factual OSINT situation report (SITREP) for the last {inp['window_hours']} hours,
based ONLY on the material below. Do not invent events. Prefer HIGH-confidence / VERIFIED stories.
Cite story indices in square brackets after each bullet, e.g. "... [3][7]".

STORIES:
{chr(10).join(lines) or '(none)'}

CONTRADICTIONS FLAGGED BY THE VERIFIER:
{chr(10).join(contra) or '(none)'}

LEADER STATEMENTS (cached):
{chr(10).join(stmts) or '(none)'}

Return ONLY a JSON object:
{{
  "headline": "<one line, max 15 words>",
  "assessment": "<2-3 sentence overall assessment>",
  "top_developments": ["<bullet with [indices]>", ...max 6],
  "contradictions": ["<what is disputed and by whom>", ...max 4],
  "leader_statements": ["<leader: signal>", ...max 4],
  "watch_items": ["<what to watch next 24h>", ...max 4]
}}"""


def _fallback_sections(inp: dict) -> dict:
    """Deterministic brief when the LLM is unavailable (never an empty page)."""
    top = [f"{(s.get('titles') or [''])[0]} [{i}]" for i, s in enumerate(inp["stories"][:6])]
    return {
        "headline": f"{inp['counts']['stories']} stories across {len(inp['regions'])} regions — LLM summary unavailable",
        "assessment": "Automatic summary unavailable; the bullets below are the top archived stories by confidence.",
        "top_developments": top,
        "contradictions": [f"{c.get('conflict')}" for c in inp["contradictions"][:4]],
        "leader_statements": [f"{st.get('leader')}: {(st.get('statement') or '')[:120]}" for st in inp["statements"][:4]],
        "watch_items": [],
        "llm": False,
    }


def _coerce(sections) -> dict | None:
    if not isinstance(sections, dict):
        return None
    out = {"headline": str(sections.get("headline", "")).strip()[:200],
           "assessment": str(sections.get("assessment", "")).strip()[:1200], "llm": True}
    for k in SECTIONS:
        v = sections.get(k)
        out[k] = [str(x).strip()[:400] for x in v if str(x).strip()][:6] if isinstance(v, list) else []
    return out if out["headline"] else None


def build_brief(hours: int = BRIEF_WINDOW_HOURS, llm=chat_json, force: bool = False) -> dict:
    if not force:
        cached = get_cached_brief(BRIEF_CACHE_HOURS)
        if cached:
            cached["cached"] = True
            return cached
    inp = gather_inputs(hours)
    sections = None
    if inp["counts"]["stories"]:
        try:
            sections = _coerce(llm(_prompt(inp), max_tokens=1200))
        except LLMError as e:
            print(f"⚠️ brief LLM failed: {e}")
    if sections is None:
        sections = _fallback_sections(inp)
    brief = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "window_hours": hours,
        "model": OPENROUTER_MODEL if sections.get("llm") else None,
        "counts": inp["counts"],
        "regions": inp["regions"],
        "queries": inp["queries"],
        "disputed_claims": inp["disputed_claims"][:8],
        "sections": sections,
        "stories": [{"title": (s.get("titles") or [""])[0], "confidence": s.get("confidence"), "verdict": s.get("verdict"),
                     "url": ((s.get("articles") or [{}])[0]).get("url"), "query": s.get("query"),
                     "country": (s.get("geo") or {}).get("country")} for s in inp["stories"][:40]],
        "cached": False,
    }
    save_brief(brief)
    return brief


def to_markdown(b: dict) -> str:
    s = b["sections"]
    c = b["counts"]
    md = [f"# SENTINEL Intelligence Brief — {b['generated_at'][:16].replace('T', ' ')} UTC",
          f"*Window: last {b['window_hours']}h · {c['stories']} stories · {c['sources']} sources · "
          f"{c['verified']} verified · {c['disputed']} disputed · {c['contradictions']} contradictions*",
          "", f"## {s.get('headline', '')}", "", s.get("assessment", ""), ""]
    titles = {"top_developments": "Top developments", "contradictions": "Contradictions",
              "leader_statements": "Leader statements", "watch_items": "Watch items (next 24h)"}
    for k in SECTIONS:
        if s.get(k):
            md += [f"## {titles[k]}"] + [f"- {x}" for x in s[k]] + [""]
    if b.get("regions"):
        md += ["## Active regions", ", ".join(f"{r} ({n})" for r, n in b["regions"]), ""]
    md += ["## Sources"] + [f"[{i}] {st['title']} — {st.get('confidence')} · {st.get('verdict')}"
                            + (f" · {st['url']}" if st.get("url") else "") for i, st in enumerate(b["stories"])]
    if not s.get("llm"):
        md += ["", "_LLM summary unavailable for this brief; bullets are deterministic._"]
    md += ["", "_Generated by SENTINEL AI from public sources. Not affiliated with any government._"]
    return "\n".join(md)


def to_telegram(b: dict) -> str:
    s = b["sections"]
    c = b["counts"]
    out = [f"🗞 <b>SENTINEL BRIEF</b> — last {b['window_hours']}h", f"<b>{html.escape(s.get('headline', ''))}</b>",
           html.escape(s.get("assessment", "")), "",
           f"📊 {c['stories']} stories · {c['verified']} verified · {c['disputed']} disputed · {c['contradictions']} contradictions", ""]
    if s.get("top_developments"):
        out.append("<b>Top developments</b>")
        out += [f"• {html.escape(x)}" for x in s["top_developments"][:5]]
    if s.get("contradictions"):
        out += ["", "<b>⚡ Contradictions</b>"] + [f"• {html.escape(x)}" for x in s["contradictions"][:3]]
    if s.get("watch_items"):
        out += ["", "<b>👁 Watch</b>"] + [f"• {html.escape(x)}" for x in s["watch_items"][:3]]
    if PUBLIC_SITE_URL:
        out += ["", f"{html.escape(PUBLIC_SITE_URL)}#/brief"]
    return "\n".join(out)


def send_brief(send=telegram.send_message, force: bool = False) -> dict:
    b = build_brief(force=force)
    ok = send(to_telegram(b))
    return {"sent": bool(ok), "generated_at": b["generated_at"], "cached": b.get("cached", False)}


_thread = None


def _loop():
    while True:
        time.sleep(BRIEF_INTERVAL_HOURS * 3600)
        try:
            if telegram.configured():
                print(f"🗞 brief push: {send_brief(force=True)}")
        except Exception as e:
            print(f"🗞 brief push crashed: {e}")


def start_scheduler() -> bool:
    global _thread
    if BRIEF_INTERVAL_HOURS <= 0 or not telegram.configured() or _thread is not None:
        return False
    _thread = threading.Thread(target=_loop, name="brief", daemon=True)
    _thread.start()
    return True
