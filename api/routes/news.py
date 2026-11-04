import asyncio
import json
import queue
import threading

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse, PlainTextResponse
from pydantic import BaseModel as _BM

from api.models.news_model import (NewsRequest, NewsResponse, TimelineResponse, GraphResponse, BriefResponse,
                                   StatsResponse, SourceReliability)
from database import mongo_available, get_recent_news, get_all_stories, get_recent_queries, get_cached_results, list_briefs
from config import NEWS_CACHE_HOURS, APP_VERSION, DEMO_MODE
from services.news_service import run_news_query, NoArticles, STAGES
from services import watchlist as wl
from services import brief as brief_svc
from services.timeline import timeline_for
from services.graph import build_graph
from services.reliability import reliability_report
from tools import telegram
from tools.llm import budget_status
from tools.report import news_markdown
from api import metrics
from api.security import limiter_backend

router = APIRouter()


@router.post("/news", response_model=NewsResponse)
async def get_news(request: NewsRequest):
    try:
        print(f"\n🌐 API Request: {request.query}")
        result = await asyncio.to_thread(run_news_query, request.query, NEWS_CACHE_HOURS)
        return NewsResponse(**{k: v for k, v in result.items() if k in NewsResponse.model_fields})
    except NoArticles:
        raise HTTPException(status_code=404, detail="No articles found!")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _sse(event: str, data) -> str:
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


@router.post("/news/stream")
async def get_news_stream(request: NewsRequest):
    """
    Same pipeline as POST /news, but as Server-Sent Events: one `stage` event per pipeline step
    (so the UI can show "Collecting… Judging contradictions… Geotagging…") then a final `result`
    (or `error`). The pipeline runs in a worker thread; events are relayed through a queue.
    """
    q: queue.Queue = queue.Queue()

    def on_stage(name, detail=""):
        q.put(("stage", {"stage": name, "detail": detail}))

    def work():
        try:
            result = run_news_query(request.query, cache_hours=NEWS_CACHE_HOURS, on_stage=on_stage)
            q.put(("result", {k: v for k, v in result.items() if k != "fresh"} | {"fresh": result.get("fresh")}))
        except NoArticles:
            q.put(("error", {"detail": "No articles found!", "status": 404}))
        except Exception as e:  # pragma: no cover - surfaced to the client
            q.put(("error", {"detail": str(e), "status": 500}))
        q.put(None)

    threading.Thread(target=work, daemon=True).start()

    async def gen():
        yield _sse("stages", {"stages": [{"id": s, "label": l} for s, l in STAGES]})
        while True:
            item = await asyncio.to_thread(q.get)
            if item is None:
                break
            yield _sse(*item)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/news/timeline", response_model=TimelineResponse)
async def news_timeline(q: str = Query(..., min_length=1), days: int = Query(7, ge=1, le=90)):
    """How a query's stories evolved across archived runs (confidence / verdict per run)."""
    return timeline_for(q, days=days)


@router.get("/news/queries")
async def news_queries(days: int = Query(7, ge=1, le=90)):
    return {"queries": get_recent_queries(hours=days * 24)}


@router.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "SENTINEL AI",
        "version": APP_VERSION,
        "database": ("in-memory (DEMO_MODE)" if DEMO_MODE else
                     "MongoDB connected ✅" if mongo_available() else "MongoDB unreachable ⚠️ (caching disabled)"),
        "rate_limiter": limiter_backend(),
        "demo_mode": DEMO_MODE,
        "llm_budget": budget_status(),
    }


@router.get("/recent")
async def get_recent():
    recent = get_recent_news(hours=24)
    return {
        "status": "success",
        "total": len(recent),
        "searches": recent
    }


@router.get("/stats", response_model=StatsResponse)
async def stats():
    """Runtime counters for the frontend status panel (LLM calls / tokens / cost, latency per route)."""
    return {**metrics.snapshot(), "budget": budget_status()}


@router.get("/sources", response_model=dict)
async def sources(hours: int = Query(24 * 30, ge=1, le=24 * 365)):
    """Per-outlet reliability learned from the archive (see services/reliability.py for the formula + caveats)."""
    rep = await asyncio.to_thread(reliability_report, hours)
    rep["sources"] = [SourceReliability(**r).model_dump() for r in rep["sources"]]
    return rep


# ── Knowledge graph ─────────────────────────────────────────────────────────
@router.get("/graph", response_model=GraphResponse, response_model_by_alias=True)
async def graph(q: str | None = None, hours: int = Query(24, ge=1, le=24 * 30)):
    """Stories ↔ entities ↔ countries from archived searches (no LLM call here)."""
    return build_graph(get_all_stories(hours), query=q)


# ── Intelligence brief ──────────────────────────────────────────────────────
@router.get("/brief", response_model=BriefResponse, response_model_exclude_none=False)
async def get_brief(refresh: bool = False, format: str = "json"):
    b = await asyncio.to_thread(brief_svc.build_brief, brief_svc.BRIEF_WINDOW_HOURS, brief_svc.chat_json, refresh)
    if format == "md":
        return PlainTextResponse(brief_svc.to_markdown(b), media_type="text/markdown; charset=utf-8",
                                 headers={"Content-Disposition": 'attachment; filename="sentinel-brief.md"'})
    return b


@router.get("/brief/history")
async def brief_history():
    return {"briefs": list_briefs()}


@router.post("/brief/send")
async def send_brief():
    if not telegram.configured():
        raise HTTPException(status_code=503, detail="Telegram not configured")
    return await asyncio.to_thread(brief_svc.send_brief)


# ── Export ──────────────────────────────────────────────────────────────────
@router.get("/export/news")
async def export_news(q: str = Query(..., min_length=1), format: str = "md"):
    """Download the most recent archived run of a query (never triggers a new search)."""
    cached = get_cached_results(q, hours=24 * 30)
    if not cached:
        raise HTTPException(status_code=404, detail="No archived search for that query — run it first")
    if format == "json":
        return cached
    fname = "".join(ch if ch.isalnum() else "-" for ch in q.lower())[:40] or "report"
    return PlainTextResponse(news_markdown(cached), media_type="text/markdown; charset=utf-8",
                             headers={"Content-Disposition": f'attachment; filename="sentinel-{fname}.md"'})


# ── Watchlist ───────────────────────────────────────────────────────────────
class WatchRequest(_BM):
    query: str


@router.get("/watchlist")
async def watchlist_list():
    return {"watches": wl.list_watches(), "telegram_configured": telegram.configured(),
            "interval_minutes": __import__("config").WATCHLIST_INTERVAL_MINUTES}


@router.post("/watchlist")
async def watchlist_add(req: WatchRequest):
    try:
        return wl.add_watch(req.query)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/watchlist")
async def watchlist_remove(query: str):
    if not wl.remove_watch(query):
        raise HTTPException(status_code=404, detail="not on watchlist")
    return {"status": "removed", "query": query}


@router.post("/watchlist/run")
async def watchlist_run():
    """Run all watches now (also the hook for an external cron)."""
    return await asyncio.to_thread(wl.run_once)


@router.post("/watchlist/test-alert")
async def watchlist_test_alert():
    ok = telegram.send_message("✅ SENTINEL AI connected — alerts will arrive here.")
    if not ok:
        raise HTTPException(status_code=503, detail="Telegram not configured or rejected the message")
    return {"status": "sent"}
