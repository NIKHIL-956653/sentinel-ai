# SENTINEL AI — threat model

This is the document AI code generators do not write unless asked. It answers: *what can go wrong,
who would make it go wrong, what we do about it, and what we knowingly accept.* Review it whenever a
feature touches an input, an outbound call, or money.

## 1. What we are protecting

| Asset | Why it matters |
|---|---|
| API credit (Tavily, OpenRouter) | The only thing that directly costs money. Every fresh search ≈ 1 Tavily call + 4 LLM calls. |
| Availability | Public demo; a stalled worker or a flood takes the whole app down. |
| Output integrity | The product's promise is "verified vs disputed". If an attacker can make lies look VERIFIED, the product is worthless. |
| Secrets | API keys, Telegram bot token, Mongo URI. |
| Users' data | Minimal: watchlist queries and search history (no accounts). Still worth not leaking. |

Out of scope: classified material (none), PII (none collected), payments (none).

## 2. Who would attack it

1. **Drive-by scripts / scrapers** — hit any open endpoint in a loop.
2. **Cost attackers** — deliberately burn LLM credit (many IPs, long queries, parallel streams).
3. **Content attackers** — publish or edit a page that the pipeline will ingest, to steer the LLM (prompt injection) or poison the archive.
4. **Curious users** — view-source, try to reach other users' watches, try the API without the UI.
5. **Insiders / us** — commit a key, misconfigure CORS, deploy with `TRUST_PROXY` wrong.

## 3. Trust boundaries

```
 browser ──(X-API-Key, public)──▶ FastAPI ──▶ Tavily / Wikipedia / World Bank (untrusted content)
                                   │  └────▶ OpenRouter (untrusted output, trusted transport)
                                   └──▶ MongoDB (trusted, private network)   └──▶ Telegram (outbound only)
```
Everything that comes back from the right-hand side is **data, never instructions**. Everything the
browser sends is attacker-controlled, including headers.

## 4. Threats, controls, residual risk

| # | Threat | Control (where) | Residual / accepted |
|---|---|---|---|
| T1 | Flood of expensive requests from one IP | Sliding-window limits per IP, tighter bucket for Tavily/LLM endpoints (`api/security.py`) | Window is per process unless `REDIS_URL` is set |
| T2 | Rate-limit bypass by spoofing `X-Forwarded-For` | Header only honoured when `TRUST_PROXY=true` (behind a proxy that overwrites it) | Misconfiguration risk → `.env.example` and `render.yaml` document it |
| T3 | Cost attack from many IPs | `PIPELINE_MAX_CONCURRENT` per process (503 + Retry-After); `LLM_DAILY_BUDGET_USD` hard ceiling in `tools/llm.py` — all callers fall back deterministically; `MAX_WATCHES`; `MAX_QUERY_LENGTH` | Budget counter is per process; a cluster needs it in Redis too (open item) |
| T4 | API-key timing attack | `hmac.compare_digest` | The key is visible in the static frontend by design: it is a speed bump, not auth |
| T5 | Prompt injection via article text | Untrusted text wrapped in «» with an explicit "data, not instructions" note; **structural validation** of every LLM output: indices range-checked, types checked, lists capped, free text truncated (`parse_*` in `tools/claims.py`, `entities.py`, `geotag.py`, `verifier_agent.py`) | The judge can still be *persuaded* (e.g. mark a false pair as contradiction). Mitigation is the eval set + method labels in the UI, not a guarantee |
| T6 | Archive poisoning (a fake outlet gets into Tavily results) | Tavily restricted to `TAVILY_INCLUDE_DOMAINS`; verdict requires a trusted-list outlet; `services/reliability.py` exposes each outlet's corroboration history | Trusted list is hand-written; reliability scores partly depend on it (documented) |
| T7 | XSS from LLM / article text in the UI | `esc()` on every backend string before `innerHTML`; `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` headers | No CSP yet (inline scripts/styles in the static UI) — open item |
| T8 | SSRF | No endpoint fetches a user-supplied URL; grounding only calls Wikipedia with LLM-provided *titles*, exports only read the archive | — |
| T9 | NoSQL injection | Queries are strings in exact-match or `re.escape`d regex; Pydantic models on bodies | — |
| T10 | Stalled upstream pins a worker | Timeouts on OpenRouter (`LLM_TIMEOUT_SECONDS`), Tavily / Wikipedia (`HTTP_TIMEOUT_SECONDS`), Telegram (10 s) | — |
| T11 | Secret leakage | `.env` git-ignored; keys never returned by any endpoint; `app-config.js` only exposes the (public by design) frontend key | Logs include query strings; do not log bodies |
| T12 | Unauthorised watchlist changes / Telegram spam | Same API key gates it; `MAX_WATCHES`; Telegram only sends to the configured chat | No per-user ownership — anyone with the key shares one watchlist (design limit, see SYSTEM_DESIGN) |
| T13 | Denial via huge archive (timeline / graph scans) | Mongo indexes ensured at startup; `limit`s on history queries; graph capped at 60 stories | No retention policy yet — add a TTL index when the archive matters (open item) |
| T14 | Supply chain | Pinned versions in `requirements.txt`; Docker runs as non-root; `pip-audit` not yet in CI | Open item |
| T15 | Misleading output presented as fact | Every LLM-derived field is labelled (`method`, `grounded`, `llm: false` fallbacks, "AI-GENERATED · UNVERIFIED"); DEMO_MODE banner | Users may still over-trust; the UI copy says so |

## 5. How to find the next one (the process, not the list)

1. **Enumerate inputs**: every request field, header, and every byte that comes back from a third party. Ask of each: *who controls this, and what happens if it is 10 MB, empty, or contains instructions?*
2. **Follow the money**: list every code path that calls a paid API. Each needs a per-IP limit, a global cap, and a fallback.
3. **Enumerate outputs**: every place a string reaches a browser, a Telegram message, or a prompt. Escape / delimit / validate at that boundary.
4. **Try to break it cheaply**: `curl` with a spoofed `X-Forwarded-For`, a 50 kB query, 20 parallel `/news/stream`, an article whose text says "ignore previous instructions". Each of these found a real gap in this codebase before the fixes above.
5. **Write the residual risk down** (this table). A risk you accepted knowingly is a decision; one you never noticed is a vulnerability.

## 6. Checklist before a public deploy

- [ ] `SENTINEL_API_KEY` set; `ALLOWED_ORIGINS` set to your origin
- [ ] `TRUST_PROXY=true` only if a proxy sets `X-Forwarded-For`
- [ ] `LLM_DAILY_BUDGET_USD` set to what you can afford to lose in a day
- [ ] `DEMO_MODE` is **not** set
- [ ] `/metrics` scraped by you, or fronted by the proxy (it leaks usage, not secrets)
- [ ] Mongo on a private network / Atlas with an allowlist, not `0.0.0.0/0` forever
- [ ] Telegram bot token rotated if it was ever pasted anywhere
