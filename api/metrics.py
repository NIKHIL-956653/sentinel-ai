"""
Observability without dependencies.

- `record_request(route, status, seconds)`  — called by the HTTP middleware for every request
- `record_llm(prompt_tokens, completion_tokens, seconds, cost, ok)` — called by tools/llm.py
- `prometheus_text()` — Prometheus exposition format for GET /metrics
- `snapshot()`        — JSON for GET /api/v1/stats (frontend "system status" panel)

In-process and single-instance (like the rate limiter). Thread-safe via one lock.
"""
import threading
import time
from collections import defaultdict

from config import LLM_PRICE_IN_PER_M, LLM_PRICE_OUT_PER_M, OPENROUTER_MODEL

_lock = threading.Lock()
_started = time.time()

# requests: (route, status) → count ; latency: route → [count, sum, buckets]
_req_count = defaultdict(int)
_req_latency = defaultdict(lambda: {"count": 0, "sum": 0.0, "max": 0.0})
_BUCKETS = (0.1, 0.5, 1, 2.5, 5, 10, 30)
_req_buckets = defaultdict(lambda: defaultdict(int))

_llm = {"calls": 0, "errors": 0, "prompt_tokens": 0, "completion_tokens": 0,
        "seconds": 0.0, "cost_usd": 0.0, "cost_is_estimate": False}

_pipeline = {"searches": 0, "cache_hits": 0, "stories": 0, "contradictions": 0}


def _route_key(path: str) -> str:
    """Collapse path params so /country/India and /country/Iran share a series."""
    parts = path.strip("/").split("/")
    out = []
    for i, p in enumerate(parts):
        # keep the first 3 segments (api / v1 / resource); everything after is a parameter
        out.append(p if i < 3 else "{param}")
    return "/" + "/".join(out)


def record_request(path: str, status: int, seconds: float) -> None:
    key = _route_key(path)
    with _lock:
        _req_count[(key, status)] += 1
        lat = _req_latency[key]
        lat["count"] += 1
        lat["sum"] += seconds
        lat["max"] = max(lat["max"], seconds)
        for b in _BUCKETS:
            if seconds <= b:
                _req_buckets[key][b] += 1
        _req_buckets[key]["inf"] += 1


def estimate_cost(prompt_tokens: int, completion_tokens: int) -> float:
    return (prompt_tokens or 0) / 1e6 * LLM_PRICE_IN_PER_M + (completion_tokens or 0) / 1e6 * LLM_PRICE_OUT_PER_M


def record_llm(prompt_tokens: int = 0, completion_tokens: int = 0, seconds: float = 0.0,
               cost: float | None = None, ok: bool = True) -> None:
    with _lock:
        _llm["calls"] += 1
        if not ok:
            _llm["errors"] += 1
        _llm["prompt_tokens"] += int(prompt_tokens or 0)
        _llm["completion_tokens"] += int(completion_tokens or 0)
        _llm["seconds"] += seconds
        if cost is not None:
            _llm["cost_usd"] += float(cost)
        else:
            _llm["cost_usd"] += estimate_cost(prompt_tokens, completion_tokens)
            _llm["cost_is_estimate"] = True


def record_search(cache_hit: bool, stories: int = 0, contradictions: int = 0) -> None:
    with _lock:
        _pipeline["searches"] += 1
        if cache_hit:
            _pipeline["cache_hits"] += 1
        _pipeline["stories"] += stories
        _pipeline["contradictions"] += contradictions


def reset() -> None:
    with _lock:
        _req_count.clear(); _req_latency.clear(); _req_buckets.clear()
        for k in _llm:
            _llm[k] = 0.0 if isinstance(_llm[k], float) else (False if isinstance(_llm[k], bool) else 0)
        for k in _pipeline:
            _pipeline[k] = 0


def snapshot() -> dict:
    with _lock:
        routes = {}
        for key, lat in _req_latency.items():
            errors = sum(c for (r, s), c in _req_count.items() if r == key and s >= 500)
            routes[key] = {"count": lat["count"], "avg_ms": round(lat["sum"] / lat["count"] * 1000) if lat["count"] else 0,
                           "max_ms": round(lat["max"] * 1000), "errors_5xx": errors}
        return {
            "uptime_s": round(time.time() - _started),
            "model": OPENROUTER_MODEL,
            "llm": {**_llm, "cost_usd": round(_llm["cost_usd"], 4),
                    "avg_ms": round(_llm["seconds"] / _llm["calls"] * 1000) if _llm["calls"] else 0},
            "pipeline": dict(_pipeline),
            "routes": routes,
        }


def prometheus_text() -> str:
    lines = [
        "# HELP sentinel_uptime_seconds Seconds since process start", "# TYPE sentinel_uptime_seconds gauge",
        f"sentinel_uptime_seconds {time.time() - _started:.0f}",
        "# HELP sentinel_http_requests_total HTTP requests by route and status", "# TYPE sentinel_http_requests_total counter",
    ]
    with _lock:
        for (route, status), c in sorted(_req_count.items()):
            lines.append(f'sentinel_http_requests_total{{route="{route}",status="{status}"}} {c}')
        lines += ["# HELP sentinel_http_request_duration_seconds Request latency", "# TYPE sentinel_http_request_duration_seconds histogram"]
        for route, buckets in sorted(_req_buckets.items()):
            for b in _BUCKETS:
                lines.append(f'sentinel_http_request_duration_seconds_bucket{{route="{route}",le="{b}"}} {buckets[b]}')
            lines.append(f'sentinel_http_request_duration_seconds_bucket{{route="{route}",le="+Inf"}} {buckets["inf"]}')
            lat = _req_latency[route]
            lines.append(f'sentinel_http_request_duration_seconds_sum{{route="{route}"}} {lat["sum"]:.4f}')
            lines.append(f'sentinel_http_request_duration_seconds_count{{route="{route}"}} {lat["count"]}')
        lines += [
            "# TYPE sentinel_llm_calls_total counter", f"sentinel_llm_calls_total {_llm['calls']}",
            "# TYPE sentinel_llm_errors_total counter", f"sentinel_llm_errors_total {_llm['errors']}",
            "# TYPE sentinel_llm_tokens_total counter",
            f'sentinel_llm_tokens_total{{kind="prompt"}} {_llm["prompt_tokens"]}',
            f'sentinel_llm_tokens_total{{kind="completion"}} {_llm["completion_tokens"]}',
            "# TYPE sentinel_llm_cost_usd_total counter", f"sentinel_llm_cost_usd_total {_llm['cost_usd']:.6f}",
            "# TYPE sentinel_llm_seconds_total counter", f"sentinel_llm_seconds_total {_llm['seconds']:.3f}",
            "# TYPE sentinel_searches_total counter",
            f'sentinel_searches_total{{result="fresh"}} {_pipeline["searches"] - _pipeline["cache_hits"]}',
            f'sentinel_searches_total{{result="cache_hit"}} {_pipeline["cache_hits"]}',
            "# TYPE sentinel_stories_total counter", f"sentinel_stories_total {_pipeline['stories']}",
            "# TYPE sentinel_contradictions_total counter", f"sentinel_contradictions_total {_pipeline['contradictions']}",
        ]
    return "\n".join(lines) + "\n"
