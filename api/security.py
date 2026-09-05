"""
Request protection for a public deployment.

Two layers:
1. API key — if SENTINEL_API_KEY is set, /api/v1/* (except /health) requires header X-API-Key.
   Honest note: the frontend is static, so the key it sends is visible to anyone who views source.
   It stops casual scripts and lets you rotate/kill access; it is NOT user authentication.
2. Rate limit — sliding window per client IP, in memory. Two buckets: a general one and a tighter one
   for endpoints that spend Tavily/LLM credits. Single-instance only; for multiple instances move the
   window store to Redis.
"""
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from config import SENTINEL_API_KEY, RATE_LIMIT_PER_MINUTE, EXPENSIVE_LIMIT_PER_MINUTE

PROTECTED_PREFIX = "/api/v1"
OPEN_PATHS = {"/api/v1/health"}
EXPENSIVE_PREFIXES = (
    "/api/v1/news", "/api/v1/country", "/api/v1/weapons", "/api/v1/special-forces",
    "/api/v1/leaders", "/api/v1/compare-analysis", "/api/v1/leader-analysis",
    "/api/v1/watchlist/run",
)


class SlidingWindowLimiter:
    """Allow at most `limit` events per `window` seconds per key."""

    def __init__(self, limit: int, window: float = 60.0):
        self.limit = limit
        self.window = window
        self._hits: dict[str, deque] = defaultdict(deque)

    def check(self, key: str, now: float | None = None) -> tuple[bool, float]:
        """Returns (allowed, retry_after_seconds)."""
        now = time.monotonic() if now is None else now
        q = self._hits[key]
        cutoff = now - self.window
        while q and q[0] <= cutoff:
            q.popleft()
        if len(q) >= self.limit:
            return False, max(0.0, q[0] + self.window - now)
        q.append(now)
        return True, 0.0

    def reset(self) -> None:
        self._hits.clear()


general_limiter = SlidingWindowLimiter(RATE_LIMIT_PER_MINUTE)
expensive_limiter = SlidingWindowLimiter(EXPENSIVE_LIMIT_PER_MINUTE)


def client_ip(request: Request) -> str:
    # Render/most PaaS put the real client in X-Forwarded-For (first hop).
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_expensive(path: str) -> bool:
    return path.startswith(EXPENSIVE_PREFIXES)


async def protect(request: Request, call_next):
    """FastAPI HTTP middleware: key check + rate limits for /api/v1/*."""
    path = request.url.path
    if not path.startswith(PROTECTED_PREFIX) or path in OPEN_PATHS or request.method == "OPTIONS":
        return await call_next(request)

    if SENTINEL_API_KEY and request.headers.get("x-api-key", "") != SENTINEL_API_KEY:
        return JSONResponse({"detail": "Missing or invalid API key (X-API-Key)"}, status_code=401)

    ip = client_ip(request)
    allowed, retry = general_limiter.check(ip)
    if allowed and is_expensive(path):
        allowed, retry = expensive_limiter.check(ip)
    if not allowed:
        return JSONResponse(
            {"detail": "Rate limit exceeded — try again shortly"},
            status_code=429,
            headers={"Retry-After": str(int(retry) + 1)},
        )
    return await call_next(request)
