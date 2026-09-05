from fastapi import APIRouter, HTTPException
from api.models.news_model import NewsRequest, NewsResponse
from database import mongo_available
from config import NEWS_CACHE_HOURS
from services.news_service import run_news_query, NoArticles

router = APIRouter()

@router.post("/news", response_model=NewsResponse)
async def get_news(request: NewsRequest):
    try:
        print(f"\n🌐 API Request: {request.query}")
        result = run_news_query(request.query, cache_hours=NEWS_CACHE_HOURS)
        return NewsResponse(**{k: v for k, v in result.items() if k != "fresh"})
    except NoArticles:
        raise HTTPException(status_code=404, detail="No articles found!")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    return {
        "status": "online",
        "service": "SENTINEL AI",
        "version": "2.0.0",
        "database": "MongoDB connected ✅" if mongo_available() else "MongoDB unreachable ⚠️ (caching disabled)"
    }

@router.get("/recent")
async def get_recent():
    from database import get_recent_news
    recent = get_recent_news(hours=24)
    return {
        "status": "success",
        "total": len(recent),
        "searches": recent
    }


# ── Watchlist ───────────────────────────────────────────────────────────────
from pydantic import BaseModel as _BM
from services import watchlist as wl
from tools import telegram


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
    return wl.run_once()


@router.post("/watchlist/test-alert")
async def watchlist_test_alert():
    ok = telegram.send_message("✅ SENTINEL AI connected — alerts will arrive here.")
    if not ok:
        raise HTTPException(status_code=503, detail="Telegram not configured or rejected the message")
    return {"status": "sent"}
