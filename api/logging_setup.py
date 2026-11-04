"""
Structured request logging. LOG_FORMAT=json emits one JSON object per request (ingestible by
Render / Loki / Datadog); the default "text" keeps the readable console line.
"""
import json
import logging
import sys
import time
from datetime import datetime, timezone

from config import LOG_FORMAT

log = logging.getLogger("sentinel")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
                   "level": record.levelname, "logger": record.name, "msg": record.getMessage()}
        extra = getattr(record, "extra", None)
        if isinstance(extra, dict):
            payload.update(extra)
        if record.exc_info:
            payload["exc"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str)


def configure() -> None:
    if log.handlers:
        return
    handler = logging.StreamHandler(sys.stdout)
    if LOG_FORMAT == "json":
        handler.setFormatter(JsonFormatter())
    else:
        handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    log.addHandler(handler)
    log.setLevel(logging.INFO)
    log.propagate = False


async def request_logger(request, call_next):
    t0 = time.perf_counter()
    response = await call_next(request)
    ms = round((time.perf_counter() - t0) * 1000, 1)
    path = request.url.path
    if path.startswith("/api/") or path in ("/", "/metrics"):
        fwd = request.headers.get("x-forwarded-for")
        ip = fwd.split(",")[0].strip() if fwd else (request.client.host if request.client else "-")
        log.info(f"{request.method} {path} {response.status_code} {ms}ms",
                 extra={"extra": {"method": request.method, "path": path, "status": response.status_code,
                                  "ms": ms, "ip": ip, "query": request.url.query or None}})
    return response
