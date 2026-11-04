"""
Request protection for a public deployment.

Two layers:
1. API key — if SENTINEL_API_KEY is set, /api/v1/* (except /health) requires header X-API-Key.
   Honest note: the frontend is static, so the key it sends is visible to anyone who views source.
   It stops casual scripts and lets you rotate/kill access; it is NOT user authentication.
2. Rate limit — sliding window per client IP. Two buckets: a general one and a tighter one for
   endpoints that spend Tavily/LLM credits. In memory by default; set REDIS_URL to share the
   window across instances (sorted-set sliding window; falls back to memory if Redis is down).
"""
import time
from collections import defaultdict, deque

from fastapi import Request
from fastapi.responses import JSONResponse

from config import SENTINEL_API_KEY, RATE_LIMIT_PER_MINUTE, EXPENSIVE_LIMIT_PER_MINUTE, REDIS_URL
from api import metrics

PROTECTED_PREFIX = "/api/v1"
OPEN_PATHS = {"/api/v1/health"}
EXPENSIVE_PREFIXES = (
    "/api/v1/news", "/api/v1/country", "/api/v1/weapons", "/api/v1/special-forces",
    "/api/v1/leaders", "/api/v1/compare-analysis", "/api/v1/leader-analysis",
    "/api/v1/watchlist/run", "/api/v1/brief", "/api/v1/export/country",
)


class SlidingWindowLimiter:
    """Allow at most `limit` events per `window` seconds per key (in-process)."""

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


class RedisSlidingWindowLimiter:
    """
    Same contract, window stored in Redis (ZSET per key) so N instances share one budget.
    Any Redis error → falls back to an in-process limiter for that call (never blocks traffic).
    """

    def __init__(self, client, limit: int, window: float = 60.0, prefix: str = "sentinel:rl"):
        self.client = client
        self.limit = limit
        self.window = window
        self.prefix = prefix
        self._fallback = SlidingWindowLimiter(limit, window)

    def check(self, key: str, now: float | None = None) -> tuple[bool, float]:
        now = time.time() if now is None else now
        rkey = f"{self.prefix}:{self.window:.0f}:{key}"
        try:
            pipe = self.client.pipeline()
            pipe.zremrangebyscore(rkey, 0, now - self.window)
            pipe.zcard(rkey)
            pipe.zrange(rkey, 0, 0, withscores=True)
            _, count, oldest = pipe.execute()
            if count >= self.limit:
                oldest_ts = oldest[0][1] if oldest else now
                return False, max(0.0, oldest_ts + self.window - now)
            pipe = self.client.pipeline()
            pipe.zadd(rkey, {f"{now:.6f}": now})
            pipe.expire(rkey, int(self.window) + 1)
            pipe.execute()
            return True, 0.0
        except Exception as e:  # redis.RedisError, connection errors, …
            print(f"⚠️ Redis limiter error ({e.__class__.__name__}); using in-memory window")
            return self._fallback.check(key)

    def reset(self) -> None:
        self._fallback.reset()
        try:
            for k in self.client.scan_iter(f"{self.prefix}:*"):
                self.client.delete(k)
        except Exception:
            pass


def make_limiter(limit: int, window: float = 60.0):
    if REDIS_URL:
        try:
            import redis  # optional dependency
            client = redis.Redis.from_url(REDIS_URL, socket_connect_timeout=2, socket_timeout=2)
            client.ping()
            print(f"🔒 rate limiter: Redis ({REDIS_URL.split('@')[-1]})")
            return RedisSlidingWindowLimiter(client, limit, window)
        except Exception as e:
            print(f"⚠️ REDIS_URL set but unusable ({e.__class__.__name__}); in-memory rate limiter")
    return SlidingWindowLimiter(limit, window)


general_limiter = make_limiter(RATE_LIMIT_PER_MINUTE)
expensive_limiter = make_limiter(EXPENSIVE_LIMIT_PER_MINUTE)


def limiter_backend() -> str:
    return "redis" if isinstance(general_limiter, RedisSlidingWindowLimiter) else "memory"


def client_ip(request: Request) -> str:
    # Render/most PaaS put the real client in X-Forwarded-For (first hop).
    fwd = request.headers.get("x-forwarded-for")
    if fwd:
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def is_expensive(path: str) -> bool:
    return path.startswith(EXPENSIVE_PREFIXES)


async def protect(request: Request, call_next):
    """FastAPI HTTP middleware: key check + rate limits for /api/v1/* (+ metrics for everything)."""
    path = request.url.path
    t0 = time.perf_counter()
    if not path.startswith(PROTECTED_PREFIX) or path in OPEN_PATHS or request.method == "OPTIONS":
        resp = await call_next(request)
        if path.startswith(PROTECTED_PREFIX):
            metrics.record_request(path, resp.status_code, time.perf_counter() - t0)
        return resp

    if SENTINEL_API_KEY and request.headers.get("x-api-key", "") != SENTINEL_API_KEY:
        metrics.record_request(path, 401, time.perf_counter() - t0)
        return JSONResponse({"detail": "Missing or invalid API key (X-API-Key)"}, status_code=401)

    ip = client_ip(request)
    allowed, retry = general_limiter.check(ip)
    if allowed and is_expensive(path):
        allowed, retry = expensive_limiter.check(ip)
    if not allowed:
        metrics.record_request(path, 429, time.perf_counter() - t0)
        return JSONResponse(
            {"detail": "Rate limit exceeded — try again shortly"},
            status_code=429,
            headers={"Retry-After": str(int(retry) + 1)},
        )
    resp = await call_next(request)
    metrics.record_request(path, resp.status_code, time.perf_counter() - t0)
    return resp
