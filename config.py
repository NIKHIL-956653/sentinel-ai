import os
from dotenv import load_dotenv

load_dotenv()

# App Settings
APP_NAME = "SENTINEL AI"
APP_VERSION = "2.2.0"
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

# Behind a reverse proxy (Render, nginx, Cloudflare) that overwrites X-Forwarded-For? Then true. Otherwise
# the header is attacker-controlled and honouring it would let anyone dodge the per-IP rate limit.
TRUST_PROXY = os.getenv("TRUST_PROXY", "false").lower() == "true"
# At most this many full search pipelines in flight per process (each = Tavily + 4 LLM calls).
PIPELINE_MAX_CONCURRENT = int(os.getenv("PIPELINE_MAX_CONCURRENT", "4"))
# Hard spend ceiling: once today's LLM cost (reported or estimated) passes this, LLM calls fail fast
# with LLMError until midnight UTC. 0 = unlimited. Deterministic fallbacks keep the app usable.
LLM_DAILY_BUDGET_USD = float(os.getenv("LLM_DAILY_BUDGET_USD", "0"))
# Max saved watchlist queries (each costs a Tavily search + 4 LLM calls per interval).
MAX_WATCHES = int(os.getenv("MAX_WATCHES", "20"))
# Outbound HTTP timeouts (seconds) for Tavily / Wikipedia so a stalled upstream cannot pin a worker.
HTTP_TIMEOUT_SECONDS = int(os.getenv("HTTP_TIMEOUT_SECONDS", "20"))
# Max characters of a user query accepted by /news and the watchlist.
MAX_QUERY_LENGTH = int(os.getenv("MAX_QUERY_LENGTH", "200"))

# Demo mode: no API keys, no network — canned (clearly fictional) search results and LLM output so the
# whole UI can be explored. Never use in production; /health and the UI banner say when it is on.
DEMO_MODE = os.getenv("DEMO_MODE", "false").lower() == "true"

# Optional Redis for the rate limiter (multi-instance deployments). Empty = in-memory window.
REDIS_URL = os.getenv("REDIS_URL", "").strip()

# Logging: "text" (default, human) or "json" (one JSON object per line — for Render/Datadog/Loki)
LOG_FORMAT = os.getenv("LOG_FORMAT", "text").lower()

# Contradiction detection: "llm" = one LLM judgement per search (falls back to keyword on failure), "keyword" = heuristic only
CONTRADICTION_MODE = os.getenv("CONTRADICTION_MODE", "llm").lower()

# Claim-level verification + entity extraction (one LLM call each per fresh search). Off = skip.
CLAIMS_ENABLED = os.getenv("CLAIMS_ENABLED", "true").lower() == "true"
ENTITIES_ENABLED = os.getenv("ENTITIES_ENABLED", "true").lower() == "true"

# Daily intelligence brief (services/brief.py): cached for BRIEF_CACHE_HOURS, pushed to Telegram
# every BRIEF_INTERVAL_HOURS when a bot is configured (0 = never push automatically).
BRIEF_CACHE_HOURS = int(os.getenv("BRIEF_CACHE_HOURS", "6"))
BRIEF_INTERVAL_HOURS = int(os.getenv("BRIEF_INTERVAL_HOURS", "24"))
BRIEF_WINDOW_HOURS = int(os.getenv("BRIEF_WINDOW_HOURS", "24"))

# Approximate USD per 1M tokens, used only when OpenRouter does not return a cost (shown as "est.")
LLM_PRICE_IN_PER_M = float(os.getenv("LLM_PRICE_IN_PER_M", "0.15"))
LLM_PRICE_OUT_PER_M = float(os.getenv("LLM_PRICE_OUT_PER_M", "0.60"))

# Watchlist alert rules (services/watchlist.py): new HIGH stories always; optionally also when a claim
# becomes disputed, and when a watched query's story count jumps by ALERT_SURGE_FACTOR between runs.
ALERT_ON_DISPUTED = os.getenv("ALERT_ON_DISPUTED", "true").lower() == "true"
ALERT_SURGE_FACTOR = float(os.getenv("ALERT_SURGE_FACTOR", "2.0"))   # 0 = off

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
