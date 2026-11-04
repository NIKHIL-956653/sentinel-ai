import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response, PlainTextResponse
import json
from api.routes.news import router
from api.routes.country import router as country_router
from api.security import protect, limiter_backend
from api.logging_setup import configure as configure_logging, request_logger
from api import metrics
from config import ALLOWED_ORIGINS, SENTINEL_API_KEY, PUBLIC_SITE_URL, APP_VERSION, DEMO_MODE
from database import mongo_available, ensure_indexes
from services.watchlist import start_scheduler
from services import brief as brief_svc

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    if DEMO_MODE:
        print("🎭 DEMO_MODE: fictional data, no API keys, in-memory store")
    if ensure_indexes():
        print("🗄️  MongoDB indexes ensured")
    if start_scheduler():
        print("⏰ watchlist scheduler started")
    if brief_svc.start_scheduler():
        print("🗞 brief scheduler started")
    yield


# Initialize FastAPI app
app = FastAPI(
    title="SENTINEL AI",
    description="Military Intelligence & News Verification Platform",
    version=APP_VERSION,
    lifespan=lifespan,
)

# CORS: "*" for local dev; set ALLOWED_ORIGINS=https://your-frontend.example in production.
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials="*" not in ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Order matters: middleware registered last runs first. Logger wraps the key/limit check so
# 401/429 responses are logged too.
app.middleware("http")(protect)
app.middleware("http")(request_logger)

# Include routes
app.include_router(router, prefix="/api/v1")
app.include_router(country_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "SENTINEL AI 🕵️",
        "status": "ONLINE",
        "version": APP_VERSION,
        "database": "MongoDB ✅" if mongo_available() else "MongoDB unreachable ⚠️",
        "auth": "api-key required" if SENTINEL_API_KEY else "open (set SENTINEL_API_KEY to protect)",
        "rate_limiter": limiter_backend(),
        "demo_mode": DEMO_MODE,
        "endpoints": {
            "app": "/app",
            "news": "/api/v1/news",
            "news_stream": "/api/v1/news/stream (SSE)",
            "timeline": "/api/v1/news/timeline?q=",
            "graph": "/api/v1/graph",
            "brief": "/api/v1/brief",
            "export": "/api/v1/export/news?q=&format=md",
            "stats": "/api/v1/stats",
            "sources": "/api/v1/sources",
            "metrics": "/metrics",
            "health": "/api/v1/health",
            "recent": "/api/v1/recent",
            "docs": "/docs"
        }
    }


@app.get("/metrics", include_in_schema=False)
async def prometheus_metrics():
    """Prometheus exposition (request counts/latency per route, LLM tokens & cost, pipeline counters)."""
    return PlainTextResponse(metrics.prometheus_text(), media_type="text/plain; version=0.0.4; charset=utf-8")


@app.get("/app-config.js", include_in_schema=False)
async def app_config_js():
    """
    Runtime settings for the static frontend, generated from server env so nothing secret-ish is
    committed. The API key is visible to anyone who loads the page — by design a speed bump, not auth
    (see api/security.py). Never cached by the service worker.
    """
    body = (f"window.SENTINEL_API_KEY = {json.dumps(SENTINEL_API_KEY)};\n"
            f"window.SENTINEL_API_BASE = \"\";  /* same origin */\n"
            f"window.SENTINEL_PUBLIC_URL = {json.dumps(PUBLIC_SITE_URL)};\n"
            f"window.SENTINEL_VERSION = {json.dumps(APP_VERSION)};\n"
            f"window.SENTINEL_DEMO = {json.dumps(DEMO_MODE)};\n")
    return Response(body, media_type="application/javascript",
                    headers={"Cache-Control": "no-store"})


# Serve the static frontend from the same process at /app (one container = whole product).
_frontend_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend")
if os.path.isdir(_frontend_dir):
    app.mount("/app", StaticFiles(directory=_frontend_dir, html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
