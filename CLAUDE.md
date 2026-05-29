# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Is

SENTINEL AI is a military intelligence and news verification platform. It has two runtime components that must run simultaneously:

1. **FastAPI backend** (`api/main.py`) — handles news search, verification, and caching
2. **Streamlit frontend** (`app.py`) — the UI, calls the FastAPI backend at `http://127.0.0.1:8000`

## Running the App

```powershell
# Terminal 1: FastAPI backend
python -m uvicorn api.main:app --reload

# Terminal 2: Streamlit frontend
streamlit run app.py
```

## Environment Setup

Requires a `.env` file with:
```
TAVILY_API_KEY=...
OPENROUTER_API_KEY=...
```

Also requires MongoDB running locally at `mongodb://localhost:27017`.

Install dependencies:
```powershell
pip install -r requirements.txt
```

## Architecture

### Request Flow (News Feed)

User query → Streamlit (`app.py`) → POST `http://127.0.0.1:8000/api/v1/news` → FastAPI route → Tavily search → confidence scoring → MongoDB cache → response back to UI

### Key Modules

| File | Purpose |
|------|---------|
| `config.py` | Central config — API keys, model names, thresholds |
| `database.py` | MongoDB client + caching helpers (1-hour TTL for news, 24-hour for leader statements) |
| `tools/tavily_search.py` | Fetches news via Tavily; restricted to trusted domains (Reuters, BBC, Al Jazeera, etc.) |
| `tools/confidence_scorer.py` | Groups similar articles by title similarity, scores HIGH/MEDIUM/LOW based on how many distinct sources cover the same story |
| `tools/summarizer.py` | Calls OpenRouter LLM to summarize a single article |
| `tools/leader_tracker.py` | Searches Tavily for leader-specific queries, then uses LLM to extract quotes/sentiment as JSON |
| `tools/wikipedia_tool.py` | Scrapes Wikipedia for country military profiles |
| `tools/weapons_tool.py` | Fetches weapon details (description, specs, image) from Wikipedia |
| `tools/global_firepower.py` | Scrapes GlobalFirepower.com for military strength data |
| `api/main.py` | FastAPI app; single router mounted at `/api/v1` |

### LLM Usage

All LLM calls go through OpenRouter (`OPENROUTER_BASE_URL`) using the model defined in `config.py` (`OPENROUTER_MODEL`, currently `openai/gpt-oss-120b`). LLM responses are always parsed as JSON — the code strips markdown code fences before `json.loads()`.

### Confidence Scoring Logic

`confidence_scorer.py` groups articles using `difflib.SequenceMatcher` with a 0.3 similarity threshold on titles. Confidence is then:
- **HIGH** — 3+ distinct sources
- **MEDIUM** — 2 sources  
- **LOW** — 1 source

Thresholds are also defined in `config.py` (`HIGH_CONFIDENCE_THRESHOLD`, `LOW_CONFIDENCE_THRESHOLD`).

### MongoDB Collections

- `news_results` — cached search results (keyed by query string, 1-hour TTL)
- `country_profiles` — military profiles per country
- `leader_statements` — extracted leader quotes (24-hour TTL, full collection replaced on refresh)
