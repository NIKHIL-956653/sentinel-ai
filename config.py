import os
from dotenv import load_dotenv

load_dotenv()

# App Settings
APP_NAME = "SENTINEL AI"
APP_VERSION = "2.0.0"
DEV_MODE = os.getenv("DEV_MODE", "true").lower() == "true"

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter — ONE model for every LLM call. Override with OPENROUTER_MODEL in .env
# (e.g. OPENROUTER_MODEL=google/gemini-2.0-flash-lite-001 for a cheaper model).
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")
LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "60"))

# MongoDB — local by default; set MONGODB_URI to an Atlas connection string for deploy.
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "sentinel_ai")

# Security (see api/security.py)
# SENTINEL_API_KEY: when set, every /api/v1/* request (except /health) must send it in X-API-Key.
# Empty = open (local dev). ALLOWED_ORIGINS: comma-separated CORS allowlist; "*" = any (dev).
SENTINEL_API_KEY = os.getenv("SENTINEL_API_KEY", "").strip()
ALLOWED_ORIGINS = [o.strip() for o in os.getenv("ALLOWED_ORIGINS", "*").split(",") if o.strip()]
RATE_LIMIT_PER_MINUTE = int(os.getenv("RATE_LIMIT_PER_MINUTE", "30"))        # any endpoint, per IP
EXPENSIVE_LIMIT_PER_MINUTE = int(os.getenv("EXPENSIVE_LIMIT_PER_MINUTE", "8"))  # endpoints that call Tavily/LLM

# Contradiction detection: "llm" = one LLM judgement per search (falls back to keyword on failure), "keyword" = heuristic only
CONTRADICTION_MODE = os.getenv("CONTRADICTION_MODE", "llm").lower()

# Watchlist + Telegram alerts (services/watchlist.py, tools/telegram.py)
WATCHLIST_ENABLED = os.getenv("WATCHLIST_ENABLED", "true").lower() == "true"
WATCHLIST_INTERVAL_MINUTES = int(os.getenv("WATCHLIST_INTERVAL_MINUTES", "60"))
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
PUBLIC_SITE_URL = os.getenv("PUBLIC_SITE_URL", "").strip()   # appended to alerts, e.g. https://…/app

# Tavily Settings
TAVILY_MAX_RESULTS = 10
TAVILY_SEARCH_DEPTH = "advanced"
TAVILY_INCLUDE_DOMAINS = [
    "reuters.com",
    "bbc.com",
    "aljazeera.com",
    "defense.gov",
    "nato.int",
    "wikipedia.org"
]

# Confidence Scoring (distinct sources covering the same story)
HIGH_CONFIDENCE_THRESHOLD = 3
LOW_CONFIDENCE_THRESHOLD = 1

# Cache TTLs (hours)
NEWS_CACHE_HOURS = 1
LEADERS_CACHE_HOURS = 24
