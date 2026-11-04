# SENTINEL AI — system design

Why this document exists: with an AI assistant anyone can produce the *features* in this repo in an
afternoon. What distinguishes a product from a demo is the set of decisions below — what the system
promises, what it costs, how it fails, and what it deliberately does not do.

## 1. Requirements (what we actually promise)

**Functional**
- A query returns stories clustered from trusted outlets with a confidence (source count), a verdict
  (source trust rule), contradictions between stories, and per-story claims marked corroborated /
  single-source / disputed — each with an explanation of *why*.
- Country dossiers combine an open statistics dataset (cited, with year) with LLM-extracted text (labelled).
- Saved queries re-run on a schedule and alert on change (new HIGH story, claim became disputed, activity surge).
- Derived views over the archive: timeline, knowledge graph, daily brief, outlet reliability.

**Non-functional (numbers, not adjectives)**
| Property | Target | How we know |
|---|---|---|
| Fresh search latency | p95 < 15 s (Tavily ≈ 2–4 s, 4 LLM calls, 3 in parallel) | `/metrics` histogram, Grafana panel |
| Cached search latency | p95 < 200 ms | same |
| Cost per fresh search | ≈ 1 Tavily call + ~4k LLM tokens (≈ $0.002 on the default model) | `sentinel_llm_cost_usd_total` |
| Daily spend ceiling | `LLM_DAILY_BUDGET_USD`, hard stop | `/health → llm_budget` |
| Availability | Degrade, never 500, when Mongo / LLM / Tavily is down | fail-soft helpers; tests run with a dead Mongo |
| Correctness of deterministic parts | clustering F1 ≥ 0.8, verdict accuracy 1.0 on the eval set | CI regression gate |

## 2. Architecture

```
            ┌────────────── static frontend (/app) ──────────────┐
            │ hash router · SSE client · canvas graph · themes   │
            └───────────────┬────────────────────────────────────┘
                            │ X-API-Key, JSON / SSE
┌───────────────────────────▼────────────────────────────────────┐
│ FastAPI                                                        │
│  middleware: request-id → key check → rate limit → gate → log  │
│  routes: news (sync pipeline in a thread) · derived views      │
│  services/news_service: cache → collect → verify → enrich ∥    │
│  tools/llm: the only OpenRouter client (budget, metrics, demo) │
└──────┬──────────────┬──────────────┬───────────────────────────┘
       │              │              │
   MongoDB        Tavily/Wikipedia  OpenRouter        Telegram (outbound)
   archive+cache  (allow-listed)    (one model, env-configurable)
```

**Key decisions and why**
- *One LLM client.* Model, timeout, budget, metrics, demo mode and injection hygiene live in one file. Changing models is one env var.
- *Pipeline is a plain function.* `run_news_query()` is called by the HTTP route, the SSE route and the scheduler, so there is exactly one behaviour to test.
- *Every LLM stage is fail-soft and structurally validated.* The model returns indices and short strings; parsers range-check, type-check and cap them. A bad model answer degrades one feature, never the response.
- *Archive, not just cache.* Every run is stored; timeline / graph / brief / reliability are derived from it with **no new paid calls**. This is what turns a search box into a monitoring tool.
- *Deterministic core, LLM at the edges.* Clustering and verdicts are plain code with an eval set; LLM steps are labelled in the data (`method`, `grounded`, `llm`) and in the UI.
- *Synchronous pipeline in a worker thread with a concurrency gate*, instead of a job queue. Simpler to run on one free dyno; the gate + SSE make the wait tolerable. (See §4 for when this stops being enough.)

## 3. Data model (MongoDB)

| Collection | Shape | Index | Growth |
|---|---|---|---|
| `news_results` | one doc per run: query, timestamp, stories[] (claims, entities, geo), contradictions[] | `(query_norm, timestamp)`, `timestamp` | 1 doc / fresh search (~20–60 kB). **No TTL yet** |
| `country_profiles` | one per country | `country_key` unique | bounded (~200) |
| `weapons_detail_cache`, `special_forces` | LLM lists, grounded | `key` unique | bounded |
| `leader_statements` | latest batch | `timestamp` | replaced each refresh |
| `briefs` | one per generation | `timestamp` | 1 / 6 h |
| `watchlist` | query, seen keys, seen disputed, last_count | `query_norm` unique | capped by `MAX_WATCHES` |

## 4. Scaling and failure analysis

| Scenario | What happens today | Next step when it matters |
|---|---|---|
| Mongo down | Everything still answers; no cache, no archive views | Atlas with backups; alert on `database` in `/health` |
| LLM down / over budget | Verdicts + clustering still work; contradictions → keyword; claims/entities/geo empty; brief deterministic | — (designed) |
| Tavily down | 404 "no articles"; cached queries still served | Second search provider behind the same `search_military_news()` signature |
| 10× traffic | Per-IP limits, concurrency gate (503), budget cap | Move pipeline to a queue (RQ/Celery) with SSE reading job progress from Redis; limiter + budget in Redis; N API replicas |
| Archive at 1M runs | Indexed lookups fine; `get_all_stories(24h)` loads full docs | Project only needed fields; TTL index (e.g. 90 days) or cold storage |
| Two scheduler instances | Both run watches → duplicate alerts | Leader election via a Redis lock, or move schedules to an external cron hitting `/watchlist/run` (documented today) |

## 5. What is deliberately not built (and what it would take)

- **User accounts / per-user watchlists.** Today one API key = one shared tenant. Needs: identity (magic-link email or OAuth), `owner` on watchlist/brief docs, per-user rate limits, and a decision about who pays for whose LLM calls. The design is ready for it (every write goes through `database.py`), the product decision is not.
- **Multilingual ingestion.** Adding Arabic/Russian/Chinese outlets means a translation step before clustering and an eval set in those languages; without the eval it is a claim, not a feature.
- **Real incident geolocation.** City precision exists for ~120 named places; true geocoding needs a gazetteer service and confidence scoring.
- **Ground truth.** Nothing here can tell a well-corroborated false story from a true one. The product says "verified" meaning "independently corroborated by outlets on an allow-list"; the UI explains that rule on every story.

## 6. Operating it

- Dashboards: `docker compose --profile monitoring up` → Grafana at :3000 (requests, p95 latency by route, 5xx, LLM tokens/cost, cache hit rate, stories/contradictions).
- Logs: `LOG_FORMAT=json`, one line per request with `request_id` (echoed as `X-Request-ID`).
- Health: `/api/v1/health` reports DB, limiter backend, demo mode, LLM budget.
- Evaluation: `python eval/run_eval.py` (needs a key for the LLM rows); CI gates the deterministic rows.
- Security: `docs/THREAT_MODEL.md` — read before deploying publicly.
