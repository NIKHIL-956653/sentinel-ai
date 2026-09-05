# SENTINEL 2.0 — Military Intelligence & OSINT Platform

[![CI](https://github.com/NIKHIL-956653/sentinel-ai/actions/workflows/ci.yml/badge.svg)](https://github.com/NIKHIL-956653/sentinel-ai/actions/workflows/ci.yml)

> Open Source Intelligence platform that aggregates, verifies, and analyzes global military and geopolitical news using AI.

## Live Demo
> `https://<your-service>.onrender.com/app/` — installable on a phone (Add to Home Screen). See **Deploy** below.

## What It Does
User searches "Russia Ukraine conflict"
↓
Tavily searches 10 trusted sources
(Reuters, BBC, Al Jazeera)
↓
AI verifier scores confidence
HIGH / MEDIUM / LOW
↓
Results shown with source links
LLM judge flags stories that contradict each other

## Features

### 📰 News Feed
- Real-time OSINT news aggregation
- AI confidence scoring (HIGH/MEDIUM/LOW) with a **"WHY?" panel** on every story: which sources were trusted / unknown / unreliable, the trust score, and the exact rule that produced the verdict
- **Watchlist**: save a query, it re-runs on a schedule; new HIGH-confidence stories are pushed to **Telegram**
- **Live threat map**: every story is geotagged (LLM → country → coordinates) and plotted on the home screen; no hardcoded "conflict zones"
- Contradiction detection: an LLM judge reads all stories for a query once and flags incompatible factual claims (keyword heuristic as fallback)
- Source verification (Reuters, BBC, Al Jazeera)

### 🌍 Country Military Dossiers
- 90+ countries supported
- Budget, active personnel and rank from **World Bank open data (SIPRI/IISS, CC BY 4.0)** — every number carries its year; rank = position by military expenditure (transparent, reproducible)
- Army / Navy / Air Force branch figures are LLM estimates from the Wikipedia summary and labelled as such
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

## Tech Stack

### Frontend (SENTINEL 2.0 Cinematic UI)
- Pure HTML + CSS + JavaScript
- Matrix rain background animation
- Animated boot sequence
- Glowing HUD panels
- No framework needed!

### Backend
- **FastAPI** — REST API backend
- **Tavily** — Real-time news search (K=10)
- **OpenRouter** — one configurable LLM (`OPENROUTER_MODEL`, default `openai/gpt-oss-120b`) via `tools/llm.py`
- **MongoDB** — Caching layer (1hr TTL for news)
- **LangChain Agents** — Collector + Verifier
- **Wikipedia** — Military profile data

### AI Pipeline
Collector Agent → Tavily search (K=10 sources)
↓
Verifier Agent → Confidence scoring
↓
MongoDB cache → Fast repeated queries
↓
LLM Analysis → Weapon details, leader analysis
↓
SENTINEL UI → Cinematic display

## Architecture
```
frontend/
├── index.html         → Cinematic UI structure
├── style.css          → HUD effects, matrix rain
└── app.js             → FastAPI integration
api/
├── main.py            → FastAPI app + CORS
└── routes/
    ├── news.py        → News search endpoint
    └── country.py     → Country/weapons/leaders endpoints
agents/
├── collector_agent.py → Tavily news collector
└── verifier_agent.py  → Source-trust + contradiction verifier
tools/
├── llm.py             → Single OpenRouter client (chat / chat_json)
├── tavily_search.py   → Trusted-domain news search
├── confidence_scorer.py → Story grouping + HIGH/MEDIUM/LOW
├── wikipedia_tool.py  → Military profiles
├── global_firepower.py → Personnel / budget / equipment numbers
├── leader_tracker.py  → Leader statements
├── weapons_detail_tool.py → Weapon details (LLM, cached)
└── special_forces_tool.py → Special forces (LLM, cached)
config.py              → All settings + env vars
database.py            → MongoDB caching layer (fail-soft)
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

The keyword number is the reason the LLM judge exists; keep both in the report so the improvement is measurable, not claimed.

## Tests & CI

```powershell
pip install -r requirements-dev.txt
pytest -q                       # unit tests — no network, no database needed
python sentinel_checker.py      # HTML ids ↔ JS, routes ↔ fetch calls, imports
python eval/run_eval.py --offline
```
GitHub Actions (`.github/workflows/ci.yml`) runs all three plus a Docker build.

## Docker

```powershell
docker compose up --build       # API + frontend at http://localhost:8000/app, MongoDB included
```
The same image runs on Render/Fly/Railway: they inject `$PORT`; set the env vars from `.env.example`.

## Open data (one-time fetch)

```powershell
python scripts/fetch_open_data.py      # → data/military_open_data.json (commit it; re-run yearly)
```
Pulls World Bank indicators MS.MIL.XPND.CD, MS.MIL.XPND.GD.ZS, MS.MIL.TOTL.P1 with provenance
(source, licence, fetch date). Until it exists, dossiers say so instead of showing numbers.

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
  In-memory, single instance; move the window store to Redis if you scale out.
- **`ALLOWED_ORIGINS`** — CORS allowlist for production (`*` in dev).
- API keys never leave the server; `.env` is git-ignored.

## Confidence Scoring
HIGH   → 3+ sources corroborate
MEDIUM → 2 sources agree
LOW    → Single source only
CONTRADICTIONS → LLM judge: incompatible factual claims (keyword fallback)

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
