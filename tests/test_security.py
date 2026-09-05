import importlib

import pytest
from fastapi.testclient import TestClient

import api.security as sec
from api.security import SlidingWindowLimiter


def test_sliding_window_limits_then_recovers():
    lim = SlidingWindowLimiter(limit=3, window=60)
    assert all(lim.check("ip", now=t)[0] for t in (0, 1, 2))
    allowed, retry = lim.check("ip", now=3)
    assert not allowed and 56 <= retry <= 58
    assert lim.check("other-ip", now=3)[0]          # per-key isolation
    assert lim.check("ip", now=61)[0]               # oldest hit expired


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(sec, "SENTINEL_API_KEY", "secret")
    sec.general_limiter.reset(); sec.expensive_limiter.reset()
    monkeypatch.setattr(sec.general_limiter, "limit", 100)
    monkeypatch.setattr(sec.expensive_limiter, "limit", 2)
    import api.main as main
    monkeypatch.setattr(main, "SENTINEL_API_KEY", "secret")
    return TestClient(main.app)


def test_health_is_open_without_key(client):
    assert client.get("/api/v1/health").status_code == 200


def test_protected_route_requires_key(client):
    assert client.get("/api/v1/recent").status_code == 401
    assert client.get("/api/v1/recent", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/api/v1/recent", headers={"X-API-Key": "secret"}).status_code == 200


def test_expensive_endpoints_rate_limited(client):
    h = {"X-API-Key": "secret"}
    # /leaders is "expensive"; limit patched to 2/min. Mongo is unreachable and Tavily key is fake,
    # so the handler itself errors — we only care that the 3rd call is refused by the limiter.
    codes = [client.get("/api/v1/leaders", headers=h).status_code for _ in range(3)]
    assert codes[2] == 429
    r = client.get("/api/v1/leaders", headers=h)
    assert r.status_code == 429 and "Retry-After" in r.headers


def test_root_and_static_frontend_mounted(client):
    assert client.get("/").json()["auth"] == "api-key required"
    assert client.get("/app/").status_code == 200
    assert "SENTINEL" in client.get("/app/").text


def test_app_config_js_serves_key_and_is_not_cached(client):
    r = client.get("/app-config.js")
    assert r.status_code == 200
    assert "javascript" in r.headers["content-type"]
    assert 'window.SENTINEL_API_KEY = "secret";' in r.text
    assert r.headers["cache-control"] == "no-store"


def test_pwa_assets_served(client):
    assert client.get("/app/manifest.json").status_code == 200
    assert client.get("/app/sw.js").status_code == 200
    assert client.get("/app/icons/icon-192.png").status_code == 200
