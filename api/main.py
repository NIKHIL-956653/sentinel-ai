import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import Response
import json
from api.routes.news import router
from api.routes.country import router as country_router
from api.security import protect
from config import ALLOWED_ORIGINS, SENTINEL_API_KEY, PUBLIC_SITE_URL
from database import mongo_available
from services.watchlist import start_scheduler

from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if start_scheduler():
        print("⏰ watchlist scheduler started")
    yield


# Initialize FastAPI app
app = FastAPI(
    title="SENTINEL AI",
    description="Military Intelligence & News Verification Platform",
    version="2.0.0",
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

# API key + per-IP rate limiting (api/security.py)
app.middleware("http")(protect)

# Include routes
app.include_router(router, prefix="/api/v1")
app.include_router(country_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "SENTINEL AI 🕵️",
        "status": "ONLINE",
        "version": "2.0.0",
        "database": "MongoDB ✅" if mongo_available() else "MongoDB unreachable ⚠️",
        "auth": "api-key required" if SENTINEL_API_KEY else "open (set SENTINEL_API_KEY to protect)",
        "endpoints": {
            "app": "/app",
            "news": "/api/v1/news",
            "health": "/api/v1/health",
            "recent": "/api/v1/recent",
            "docs": "/docs"
        }
    }

@app.get("/app-config.js", include_in_schema=False)
async def app_config_js():
    """
    Runtime settings for the static frontend, generated from server env so nothing secret-ish is
    committed. The API key is visible to anyone who loads the page — by design a speed bump, not auth
    (see api/security.py). Never cached by the service worker.
    """
    body = (f"window.SENTINEL_API_KEY = {json.dumps(SENTINEL_API_KEY)};\n"
            f"window.SENTINEL_API_BASE = \"\";  /* same origin */\n"
            f"window.SENTINEL_PUBLIC_URL = {json.dumps(PUBLIC_SITE_URL)};\n")
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