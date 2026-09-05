# CLAUDE.md

Guidance for Claude Code when working in this repository.

## What This Is

SENTINEL AI (2.0) is an OSINT military-intelligence and news-verification platform. Two runtime parts:

1. **FastAPI backend** (`api/main.py`) — news search + verification, country dossiers, weapons/special-forces, leader statements, LLM analysis. Mounted at `/api/v1`.
2. **Static HTML frontend** (`frontend/index.html`, `app.js`, `style.css`) — no framework, no build step. Talks to the backend via `API_BASE` (see `window.SENTINEL_API_BASE` in `index.html`).

`legacy/` holds the original Streamlit UI and CLI. Not maintained; do not extend it.

## Running Locally

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# Terminal 1 — backend (from repo root)
python -m uvicorn api.main:app --reload

# Terminal 2 — frontend: open frontend/index.html in a browser
start frontend\index.html
```

MongoDB is optional for running (caching degrades gracefully) but expected in normal use: local `mongodb://localhost:27017` or set `MONGODB_URI` to an Atlas string.

## Environment (`.env`, see `.env.example`)

```
TAVILY_API_KEY=...
OPENROUTER_API_KEY=...
# optional
OPENROUTER_MODEL=openai/gpt-oss-120b
MONGODB_URI=mongodb://localhost:27017
```

## Architecture

### Request flow — news
Query → POST `/api/v1/news` → cache check (`database.get_cached_results`, 1h) → `CollectorAgent` (Tavily, trusted domains, K=10) → `confidence_scorer` (difflib title grouping 0.3; HIGH 3+ / MEDIUM 2 / LOW 1 distinct sources) → `VerifierAgent` (trusted/unreliable source lists → trust score → verdict; keyword-pair contradiction flags) → save to Mongo → response.

### Request flow — countries
GET `/api/v1/country/{name}` → in-process cache → Mongo `country_profiles` → `wikipedia_tool` (Wikipedia search + summary → LLM → JSON) merged with `global_firepower` scrape → saved to Mongo.

Weapons (`/weapons/{country}/{category}`), special forces (`/special-forces/{country}`), compare and leader-analysis are LLM-generated; weapons and special forces are cached in Mongo.

### Key modules

| File | Purpose |
|------|---------|
| `config.py` | All settings + env: API keys, `OPENROUTER_MODEL`, `MONGODB_URI`, thresholds, cache TTLs |
| `database.py` | Mongo client (lazy, 3s timeout, fail-soft helpers), all cache read/write functions, `get_db()` |
| `tools/llm.py` | **The only place that calls OpenRouter.** `chat()` for text, `chat_json()` for structured output (strips ``` fences). Raises `LLMError`. |
| `tools/tavily_search.py` | News search restricted to trusted domains |
| `tools/confidence_scorer.py` | Story grouping + HIGH/MEDIUM/LOW |
| `agents/collector_agent.py` / `verifier_agent.py` | Pipeline stages for `/news` |
| `tools/wikipedia_tool.py`, `tools/global_firepower.py` | Country profile data |
| `tools/weapons_detail_tool.py`, `tools/special_forces_tool.py`, `tools/leader_tracker.py`, `tools/summarizer.py` | LLM-backed features |
| `api/routes/news.py`, `api/routes/country.py` | Routers |
| `services/news_service.py` | `run_news_query()` — the pipeline (cache → collect → verify → geotag → save) shared by `/news` and the watchlist |
| `services/watchlist.py` | Mongo-backed saved queries, `run_once()` (injectable `send`/`runner` for tests), daemon scheduler started from the app lifespan |
| `tools/telegram.py` | Bot API `send_message` + `format_alert` (HTML-escaped) |
| `tools/geotag.py` | One LLM call per search → country per story → `COUNTRY_COORDS` centroid; `story["geo"]` |
| `tools/grounding.py` | Batched Wikipedia title verification → `source_url` / `grounded` on LLM-generated items |
| `tools/military_data.py` | Open statistics from `data/military_open_data.json` (ISO3-keyed; `scripts/fetch_open_data.py` creates it) |
| `api/security.py` | API-key check + per-IP sliding-window rate limits (middleware). Enforced only when `SENTINEL_API_KEY` is set |
| `sentinel_checker.py` | Static consistency checks (HTML ids ↔ JS, routes ↔ fetch calls, imports, no OpenRouter calls outside llm.py). Run `python sentinel_checker.py` |
| `tests/` | pytest suite — no network, no Mongo (conftest points MONGODB_URI at a dead port and mocks `chat_json`) |
| `eval/` | Synthetic labelled set + `run_eval.py` → `eval/results.json` (clustering F1, verdict accuracy, contradiction P/R) |
| `Dockerfile`, `docker-compose.yml` | One image = API + frontend at `/app`; compose adds Mongo |

### Contradiction detection
`VerifierAgent.check_contradictions` → LLM judge (`check_contradictions_llm`, one call per search, returns
indexed pairs) when `CONTRADICTION_MODE=llm`; falls back to `check_contradictions_keyword` on `LLMError`.
Every contradiction dict carries `method: "llm" | "keyword"`.

### Story clustering
`tools/confidence_scorer.calculate_similarity` = Jaccard over content words with ≥2 shared words,
threshold 0.15 (tuned on the eval set). Do not go back to difflib — precision collapses (see README table).

### LLM-generated content must be grounded or labelled
Weapons/special-forces items carry `grounded` + `source_url`; the UI shows a Wikipedia link or an
"AI-GENERATED · UNVERIFIED" badge. Cache keys for these carry a `_v2` suffix (object items); bump the
suffix when the item shape changes.

### Rules of the codebase
- New heavy endpoints go in `EXPENSIVE_PREFIXES` (api/security.py).
- The scraper is gone: never re-add HTML scraping of third-party sites; use the open dataset.
- Frontend → backend calls go through `apiFetch()` (adds `X-API-Key`, maps 401/429 to messages).
- Changing the verdict rule or similarity → update `eval/dataset.json` expectations and re-run `eval/run_eval.py`; paste new numbers into README.
- Never call OpenRouter directly — go through `tools/llm.py` so the model is configurable in one place.
- Never hardcode the Mongo URI — `config.MONGODB_URI`.
- Every Mongo access goes through a `database.py` helper (they are fail-soft).
- LLM JSON outputs must be type-checked (`isinstance(list/dict)`) before use.
- Frontend must not hardcode backend URLs — use `API_BASE`.

## Known limitations (be honest about these in docs)
- Keyword contradiction fallback is blunt (F1 0.24 on the eval set); the LLM judge is the real detector.
- Eval set is synthetic and small — good for regression, not a benchmark claim.
- Branch-level (army/navy/air force) figures are LLM estimates from Wikipedia text — labelled, not authoritative.
- Geotag places a story at a country centroid, not the incident location.
- Watchlist scheduler is in-process; it sleeps if the host sleeps.
- Weapons / special-forces content is LLM-generated (not from an authoritative dataset).
