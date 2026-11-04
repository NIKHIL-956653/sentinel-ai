# SENTINEL 2.2 — Military Intelligence & OSINT Platform

[![CI](https://github.com/NIKHIL-956653/sentinel-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/NIKHIL-956653/sentinel-ai/actions/workflows/ci.yml)

> Open Source Intelligence platform that aggregates, verifies, and analyzes global military and geopolitical news using AI.

## Run it
Deploys as one container (API + frontend at `/app/`, installable on a phone via *Add to Home Screen*) — see **Deploy** below.
Every screen has a shareable URL: `#/news?q=red%20sea`, `#/countries/India`, `#/compare/India/Pakistan`, `#/graph?q=…`, `#/brief`.
Press **Ctrl+K** anywhere for the command palette (`dossier india`, `compare us china`, `watch iran`, `news red sea`, `brief`, `graph`, `theme`).

## What It Does
User searches "Russia Ukraine conflict"
↓
Tavily searches 10 trusted sources
(Reuters, BBC, Al Jazeera)
↓
Articles clustered into stories → confidence HIGH / MEDIUM / LOW
↓
Verifier: source trust → verdict · LLM judge flags contradicting stories
↓
Claim extractor: 1-3 atomic claims per story, each marked corroborated / single-source / disputed
by the *other* stories · entities (people, orgs, weapons, places) → knowledge graph · geotag → map
↓
Every stage streamed live to the UI (SSE) · archived runs → story timeline · daily SITREP brief

## Features

### 📰 News Feed
- Real-time OSINT news aggregation, **streamed**: the pipeline HUD shows each stage as it runs (cache → collect → cluster → verify → LLM judge → claims → entities → geotag → save) over Server-Sent Events, with a plain-POST fallback
- **Claim-level verification**: headline similarity says outlets cover *a story*; the claim extractor says which *facts* they agree on. Each story carries 1-3 atomic claims tagged ✔ CORROBORATED (another story states it), ◌ SINGLE SOURCE, or ⚡ DISPUTED (another story asserts an incompatible fact), with the supporting / contradicting story numbers
- **Story timeline**: every run is archived; search the same query again and a strip shows how each story's confidence, verdict and disputed claims evolved run-by-run (▲ / ▼ trend)
- **Export**: Markdown or JSON report of any archived search; Print / PDF of the rendered page
- AI confidence scoring (HIGH/MEDIUM/LOW) with a **"WHY?" panel** on every story: which sources were trusted / unknown / unreliable, the trust score, and the exact rule that produced the verdict
- **Watchlist**: save a query, it re-runs on a schedule; new HIGH-confidence stories are pushed to **Telegram**
- **Live threat map**: every story is geotagged (LLM → country → coordinates) and plotted on the home screen; no hardcoded "conflict zones"
- Contradiction detection: an LLM judge reads all stories for a query once and flags incompatible factual claims (keyword heuristic as fallback)
- Source verification (Reuters, BBC, Al Jazeera)

### 🗞️ Daily Intelligence Brief (SITREP)
- One LLM call summarises the last 24h of archived searches (never spends new Tavily credits): headline, assessment, top developments with `[story]` citations, contradictions, cached leader statements, watch items, active regions, disputed claims
- Cached 6h, **Regenerate** on demand, download as Markdown, **Send to Telegram**, and an automatic daily push when a bot is configured
- Deterministic fallback when the LLM is down — the brief is never empty and says when it is not AI-written

### 🕸️ Knowledge Graph
- Entities extracted per search (person / organisation / weapon / place) are assembled into a force-directed graph with stories, geotagged countries and the tracked leaders → their countries
- Zero dependencies (canvas), drag / hover / click: a story opens its source, a country opens its dossier; filter by query and time window

### 🌍 Country Military Dossiers
- 90+ countries supported
- Budget, active personnel and rank from **World Bank open data (SIPRI/IISS, CC BY 4.0)** — every number carries its year; rank = position by military expenditure (transparent, reproducible)
- Army / Navy / Air Force branch figures are LLM estimates from the Wikipedia summary and labelled as such
- **15-year military-expenditure sparkline** per country (World Bank series, re-run `scripts/fetch_open_data.py` to populate) and a Markdown / PDF dossier export
- Clickable weapon categories:
  - 🚀 Missiles (with history — BrahMos named after Brahmaputra + Moskva!)
  - 🤿 Submarines (patrol areas, class, year)
  - ✈️ Fighter Jets (variants, history)
  - 🚂 Tanks (combat history)
  - 🛳️ Warships (notable operations)
- 🕵️ Special Forces & Intelligence Units
- Weapon and unit lists are LLM-generated, then **grounded**: each item names its Wikipedia article, we verify the article exists and link it; items that fail are shown with an explicit "AI-GENERATED · UNVERIFIED" badge

### 👤 World Leader Statements
- Real-time leader statement interception
- Sentiment analysis (Aggressive/Diplomatic/Neutral/Warning)
- Click any leader → Modal popup with full AI analysis
- Geopolitical context and assessment

### ⚔️ Military Comparison
- Select any 2 countries
- Side-by-side military stats
- AI-powered winner analysis

### 📊 Observability
- `GET /metrics` — Prometheus exposition: requests / latency histogram per route, LLM calls, tokens, cost (OpenRouter-reported or estimated), cache hit rate, stories, contradictions
- `GET /api/v1/stats` — the same as JSON; the home screen shows LLM calls / tokens / cost / cache-hit live
- `LOG_FORMAT=json` — one structured JSON line per request for Render / Loki / Datadog
- Rate limiter can share its window across instances via `REDIS_URL` (sorted-set sliding window, falls back to memory)

## Tech Stack

### Frontend (SENTINEL 2.2 Cinematic UI)
- Pure HTML + CSS + JavaScript — no framework, no build step
- Dark (HUD) and **light** themes via CSS variables; animations toggle + `prefers-reduced-motion` respected
- Hash router (shareable deep links), Ctrl+K command palette, SSE pipeline HUD, canvas knowledge graph, SVG sparklines
- Matrix rain background, animated boot sequence, glowing panels (all switchable off)

### Backend
- **FastAPI** — REST API backend
- **Tavily** — Real-time news search (K=10)
- **OpenRouter** — one configurable LLM (`OPENROUTER_MODEL`, default `openai/gpt-oss-120b`) via `tools/llm.py`
- **MongoDB** — Caching layer (1hr TTL for news) + archive for timeline / brief / graph
- **Custom agent pipeline** — Collector + Verifier (plain Python, no agent framework)
- **Wikipedia** — Military profile data; **World Bank** — open military statistics

### AI Pipeline (per search, 4 LLM calls on a cache miss)
Collector Agent → Tavily search (K=10 trusted sources) → story clustering
↓
Verifier Agent → source trust → verdict; LLM judge → contradictions (keyword fallback)
↓
Claims (1 call) → Entities (1 call) → Geotag (1 call) → MongoDB archive
↓
SENTINEL UI → streamed HUD, map, timeline, graph, brief

## Architecture
```
frontend/
├── index.html         → UI structure (9 screens, command palette)
├── style.css          → Theme tokens (dark/light), HUD effects, print styles
└── app.js             → FastAPI integration, SSE, router, graph, sparklines
api/
├── main.py            → FastAPI app, CORS, /metrics, /app-config.js
├── security.py        → API key + rate limits (memory or Redis)
├── metrics.py         → Request / LLM / pipeline counters (Prometheus + JSON)
├── logging_setup.py   → Structured request logs
└── routes/
    ├── news.py        → /news, /news/stream (SSE), /news/timeline, /graph, /brief, /export, /stats, watchlist
    └── country.py     → /country, /weapons, /special-forces, /leaders, /compare-analysis, /export/country
agents/
├── collector_agent.py → Tavily news collector
└── verifier_agent.py  → Source-trust + contradiction verifier
services/
├── news_service.py    → The pipeline (cache → collect → verify → claims → entities → geotag → save) with stage callbacks
├── brief.py           → Daily SITREP (LLM summary + deterministic fallback, Telegram push)
├── timeline.py        → Story evolution across archived runs
├── graph.py           → Knowledge graph assembly (no LLM call)
└── watchlist.py       → Saved queries + scheduler + alerts
tools/
├── llm.py             → Single OpenRouter client (chat / chat_json) + usage metrics
├── tavily_search.py   → Trusted-domain news search
├── confidence_scorer.py → Story grouping + HIGH/MEDIUM/LOW
├── claims.py          → Atomic claims + cross-source corroboration (LLM, fail-soft)
├── entities.py        → Entity extraction (LLM, fail-soft)
├── geotag.py          → Story → country → coordinates
├── grounding.py       → Wikipedia title verification for LLM lists
├── military_data.py   → World Bank open statistics (+ yearly series)
├── wikipedia_tool.py  → Military profiles
├── leader_tracker.py  → Leader statements
├── report.py          → Markdown report generators
├── telegram.py        → Bot API client
├── weapons_detail_tool.py → Weapon details (LLM, cached, grounded)
└── special_forces_tool.py → Special forces (LLM, cached, grounded)
config.py              → All settings + env vars
database.py            → MongoDB layer (fail-soft): caches, archive, briefs
eval/                  → Synthetic labelled set + harness with CI regression gate
legacy/                → Old Streamlit UI (not maintained)
```

## Setup

### 1. Clone
```bash
git clone https://github.com/NIKHIL-956653/sentinel-ai.git
cd sentinel-ai
```

### 2. Virtual environment
```bash
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Environment variables
Copy `.env.example` to `.env` and fill in:
```
OPENROUTER_API_KEY=your_key
TAVILY_API_KEY=your_key
# optional
OPENROUTER_MODEL=openai/gpt-oss-120b
MONGODB_URI=mongodb://localhost:27017     # or a MongoDB Atlas connection string
```
MongoDB is used for caching. If it is unreachable the app still runs, just without cache.

### 4. Run

**Terminal 1 — FastAPI (from the repo root):**
```powershell
python -m uvicorn api.main:app --reload
```

**Terminal 2 — Open frontend:**
```powershell
start frontend\index.html
```

**Deploying the frontend separately?** Set `window.SENTINEL_API_BASE` in `frontend/index.html` to your backend URL.

**Sanity check:** `python sentinel_checker.py` verifies HTML ids ↔ JS, routes ↔ fetch calls, imports and env.

### API at a glance
| Endpoint | What |
|---|---|
| `POST /api/v1/news` | Search + verify (JSON) |
| `POST /api/v1/news/stream` | Same, as Server-Sent Events: `stages`, `stage`…, `result` / `error` |
| `GET /api/v1/news/timeline?q=&days=` | Story evolution across archived runs |
| `GET /api/v1/graph?q=&hours=` | Knowledge graph nodes / edges from archived searches |
| `GET /api/v1/brief?refresh=&format=json\|md` · `POST /brief/send` | Daily SITREP |
| `GET /api/v1/export/news?q=&format=md\|json` · `GET /export/country/{name}` | Reports |
| `GET /api/v1/country/{name}` · `/weapons/{name}/{cat}` · `/special-forces/{name}` · `/leaders` | Dossiers |
| `GET /api/v1/stats` · `GET /metrics` | Runtime counters (JSON / Prometheus) |
| `GET/POST/DELETE /api/v1/watchlist` · `POST /watchlist/run` | Watchlist |

## Key Metrics
K=10 Tavily sources per query
1hr MongoDB TTL cache
90+ countries supported
4 weapon categories per country
Real-time leader sentiment analysis
OSINT only — public sources

## Evaluation

`eval/dataset.json` is a small **synthetic** labelled set (fictional place names, so nothing in it
describes a real event). `python eval/run_eval.py` measures the pipeline and writes `eval/results.json`;
CI runs it offline on every push.

| Component | Metric | Result |
|-----------|--------|--------|
| Story clustering (token-overlap similarity) | pairwise F1 | **0.83** (was 0.47 with the original difflib matcher) |
| Verdict rule | accuracy | **1.00** (10/10) |
| Contradictions — keyword heuristic | F1 | **0.24** (P 0.40 / R 0.17) |
| Contradictions — LLM judge | F1 | run `python eval/run_eval.py` with your key to measure your model |
| Claim corroboration — LLM | F1 | run `python eval/run_eval.py` with your key (8 labelled cases in `dataset.json → claims`) |

The keyword number is the reason the LLM judge exists; keep both in the report so the improvement is measurable, not claimed.
CI runs the offline part with a **regression gate**: `--min-clustering-f1 0.8 --min-verdict-acc 1.0` fails the build if a change degrades the deterministic pipeline.

## Tests & CI

```powershell
pip install -r requirements-dev.txt
pytest -q                       # unit tests — no network, no database needed
python sentinel_checker.py      # HTML ids ↔ JS, routes ↔ fetch calls, imports
python eval/run_eval.py --offline --min-clustering-f1 0.8 --min-verdict-acc 1.0
node --check frontend/app.js
```
GitHub Actions (`.github/workflows/ci.yml`) runs all of these plus a Docker build.

## Docker

```powershell
docker compose up --build       # API + frontend at http://localhost:8000/app, MongoDB included
```
The same image runs on Render/Fly/Railway: they inject `$PORT`; set the env vars from `.env.example`.

## Open data (one-time fetch)

```powershell
python scripts/fetch_open_data.py      # → data/military_open_data.json (commit it; re-run yearly)
```
Pulls World Bank indicators MS.MIL.XPND.CD, MS.MIL.XPND.GD.ZS, MS.MIL.TOTL.P1 (latest value) plus the
last 15 years of MS.MIL.XPND.CD for the dossier sparkline, with provenance (source, licence, fetch date).
Until it exists, dossiers say so instead of showing numbers; a dataset fetched before 2.2 has no series and
the dossier says that too.

## Watchlist + Telegram alerts

1. Create a bot with @BotFather → `TELEGRAM_BOT_TOKEN`; get your chat id from @userinfobot → `TELEGRAM_CHAT_ID`.
2. In the app: type a query → **🔔 WATCH**. **TEST TELEGRAM** sends a hello message.
3. Every `WATCHLIST_INTERVAL_MINUTES` (default 60) the backend re-runs each watch and alerts only on
   HIGH-confidence stories it has not alerted before.
   Free hosting that sleeps when idle also sleeps the scheduler — point an external cron at
   `POST /api/v1/watchlist/run` (with your `X-API-Key`) to guarantee the cadence.

## Deploy (Render + MongoDB Atlas, both free tiers)

1. **MongoDB Atlas** → Create a free M0 cluster → Database Access: add a user → Network Access: allow `0.0.0.0/0`
   (Render's IPs change) → Connect → Drivers → copy the `mongodb+srv://…` string → that is `MONGODB_URI`.
2. **Render** → New → **Blueprint** → pick this repo → Render reads `render.yaml` and asks for the
   secret values: `TAVILY_API_KEY`, `OPENROUTER_API_KEY`, `MONGODB_URI` (Telegram ones optional).
   `SENTINEL_API_KEY` is auto-generated; the frontend picks it up from `/app-config.js`, so nothing is committed.
3. First build takes ~3 min. Open `https://<service>.onrender.com/app/`.
4. **Phone**: open that URL in Chrome/Safari → menu → *Add to Home Screen*. It installs as a standalone app
   (manifest + service worker; network-first for code so every deploy shows up on next open).

Free-tier facts: the instance sleeps after 15 min idle (first request then takes ~30-50 s), and the
watchlist scheduler sleeps with it — point a free cron (e.g. cron-job.org) at
`POST https://<service>.onrender.com/api/v1/watchlist/run` with header `X-API-Key` to keep alerts flowing.
Every push to `main` redeploys automatically after CI.

## Security model (read before deploying)

- **`SENTINEL_API_KEY`** — when set, every `/api/v1/*` call (except `/health`) needs header `X-API-Key`.
  The static frontend sends `window.SENTINEL_API_KEY`, which anyone can read in view-source: it stops
  casual scripts and lets you rotate access, it is *not* user authentication.
- **Rate limiting** — sliding window per client IP: `RATE_LIMIT_PER_MINUTE` (default 30) for all
  endpoints and `EXPENSIVE_LIMIT_PER_MINUTE` (default 8) for endpoints that spend Tavily/LLM credits.
  In-memory by default; set `REDIS_URL` to share one window across instances (falls back to memory if Redis is unreachable).
- **`ALLOWED_ORIGINS`** — CORS allowlist for production (`*` in dev).
- API keys never leave the server; `.env` is git-ignored.

## Confidence Scoring
HIGH   → 3+ sources corroborate
MEDIUM → 2 sources agree
LOW    → Single source only
CONTRADICTIONS → LLM judge: incompatible factual claims (keyword fallback)
CLAIMS → per story: corroborated (another story states the same fact) / single-source / disputed

## Honest limitations
- Claims, entities, geotags, contradictions and the brief are LLM outputs: type-checked, index-validated and fail-soft, but not ground truth. The eval set is synthetic and small (regression guard, not a benchmark).
- The LLM judge / claim numbers in the table above are blank until you run the eval with your own key and model.
- Weapons / special-forces lists are LLM-generated; grounded items link to Wikipedia, the rest are labelled unverified.
- Metrics and the in-memory rate limiter are per process; use `REDIS_URL` (limits) and scrape `/metrics` per instance if you scale out.
- Geotag places a story at a country centroid, not the incident location.

## Why SENTINEL?

> "In times of conflict, no one knows the truth.
> SENTINEL cross-references multiple public sources
> and uses AI to show you what's verified,
> what's uncertain, and what's contradicted."

Not affiliated with any government or intelligence agency.
Analyzes publicly available news for educational purposes.

## Author

**Nikhil Chandra Sairam Tokala**
AI/ML Engineer | GenAI Engineer | DevOps
Dubai, UAE
[LinkedIn](https://linkedin.com/in/nikhil-chandra-133ncsr200233) |
[GitHub](https://github.com/NIKHIL-956653)
