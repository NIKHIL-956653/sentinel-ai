"""Grounding, geotag, open-data lookup, watchlist diffing, Telegram formatting, news route via service."""
import json

import pytest

from tools import grounding, geotag, military_data, telegram
from services import watchlist as wl


# ── grounding ───────────────────────────────────────────────────────────────
def test_ground_items_marks_verified_and_unverified(monkeypatch):
    monkeypatch.setattr(grounding, "verify_wikipedia_titles",
                        lambda titles, timeout=8: {"BrahMos": "https://en.wikipedia.org/wiki/BrahMos", "Made Up Missile": None})
    items = [{"name": "BrahMos", "wiki_title": "BrahMos"}, {"name": "Fake", "wiki_title": "Made Up Missile"}, {"name": "NoTitle"}, "junk"]
    out = grounding.ground_items(items)
    assert [i["grounded"] for i in out] == [True, False, False]
    assert out[0]["source_url"].endswith("/BrahMos") and out[1]["source_url"] is None
    assert grounding.grounding_summary(out) == {"total": 3, "grounded": 1, "unverified": 2}


def test_verify_titles_network_failure_is_soft(monkeypatch):
    class Boom:
        def __init__(self, *a, **k): raise grounding.requests.ConnectionError("offline")
    monkeypatch.setattr(grounding.requests, "get", lambda *a, **k: Boom())
    assert grounding.verify_wikipedia_titles(["A", "B"]) == {"A": None, "B": None}


def test_verify_titles_follows_normalisation_and_redirects(monkeypatch):
    class R:
        status_code = 200
        def json(self):
            return {"query": {
                "normalized": [{"from": "brahMos", "to": "BrahMos"}],
                "redirects": [{"from": "BrahMos", "to": "BrahMos (missile)"}],
                "pages": {"1": {"title": "BrahMos (missile)", "fullurl": "https://en.wikipedia.org/wiki/BrahMos_(missile)"},
                          "-1": {"title": "Nope", "missing": ""}}}}
    monkeypatch.setattr(grounding.requests, "get", lambda *a, **k: R())
    out = grounding.verify_wikipedia_titles(["brahMos", "Nope"])
    assert out["brahMos"].endswith("BrahMos_(missile)") and out["Nope"] is None


# ── geotag ──────────────────────────────────────────────────────────────────
def test_geotag_normalises_aliases_and_ignores_junk():
    assert geotag.geo_for("USA")["country"] == "United States"
    assert geotag.geo_for("gaza")["country"] == "Palestine"
    assert geotag.geo_for("Atlantis") is None
    tags = geotag.parse_geotags([{"i": 0, "country": "Iran"}, {"i": 0, "country": "Iraq"},  # dup index ignored
                                 {"i": 9, "country": "Iran"}, {"i": "x"}, {"i": 1, "country": "Nowhere"}], 3)
    assert list(tags) == [0] and tags[0]["country"] == "Iran" and isinstance(tags[0]["lat"], float)


def test_geotag_stories_is_fail_soft(monkeypatch):
    def fail(*a, **k): raise geotag.LLMError("down")
    monkeypatch.setattr(geotag, "chat_json", fail)
    stories = [{"titles": ["x"]}]
    geotag.geotag_stories(stories)
    assert stories[0]["geo"] is None


def test_geotag_stories_attaches_geo(monkeypatch):
    monkeypatch.setattr(geotag, "chat_json", lambda *a, **k: [{"i": 1, "country": "Ukraine"}])
    stories = [{"titles": ["a"]}, {"titles": ["b"]}]
    geotag.geotag_stories(stories)
    assert stories[0]["geo"] is None and stories[1]["geo"]["country"] == "Ukraine"


# ── open data ───────────────────────────────────────────────────────────────
def test_military_data_missing_file_is_honest(monkeypatch, tmp_path):
    monkeypatch.setattr(military_data, "DATA_PATH", str(tmp_path / "nope.json"))
    military_data._load.cache_clear()
    assert military_data.available() is False
    assert military_data.get_stats("India") is None
    assert "run scripts/fetch_open_data.py" in military_data.provenance()["source"]


def test_military_data_lookup_by_iso3(monkeypatch, tmp_path):
    f = tmp_path / "d.json"
    f.write_text(json.dumps({"_source": "test", "_license": "CC", "_fetched_at": "2026-01-01T00:00:00Z",
                             "countries": {"ARE": {"name": "United Arab Emirates",
                                                   "expenditure_usd": {"value": 2.5e10, "year": 2023},
                                                   "expenditure_gdp_pct": {"value": 5.2, "year": 2023},
                                                   "personnel_total": {"value": 65000, "year": 2022},
                                                   "rank_by_expenditure": 18}}}))
    monkeypatch.setattr(military_data, "DATA_PATH", str(f))
    military_data._load.cache_clear()
    s = military_data.get_stats("UAE")
    assert s["defense_budget"] == "$25.0B (2023)" and s["active_personnel"] == "65,000 (2022)"
    assert s["global_rank"] == 18 and "5.2%" in s["defense_budget_gdp_pct"]
    assert military_data.get_stats("Atlantis") is None
    military_data._load.cache_clear()


def test_fmt_usd():
    assert military_data.fmt_usd(1.2e12) == "$1.20T" and military_data.fmt_usd(8.6e10) == "$86.0B" and military_data.fmt_usd(5e6) == "$5M"


# ── watchlist ───────────────────────────────────────────────────────────────
def test_new_high_confidence_filters_seen_and_non_high():
    seen = {wl.story_key({"titles": ["Old story"]})}
    stories = [{"titles": ["Old story"], "confidence": "HIGH"},
               {"titles": ["New story"], "confidence": "HIGH"},
               {"titles": ["Weak story"], "confidence": "LOW"}]
    assert [s["titles"][0] for s in wl.new_high_confidence(stories, seen)] == ["New story"]


def test_run_once_alerts_only_on_new_high(monkeypatch):
    docs = [{"_id": 1, "query": "northland", "seen_keys": [wl.story_key({"titles": ["Already alerted"]})]}]
    updates = []

    class FakeColl:
        def find(self): return list(docs)
        def update_one(self, flt, upd): updates.append(upd["$set"])
    monkeypatch.setattr(wl, "watchlist_collection", FakeColl())
    monkeypatch.setattr(wl, "_safe", lambda fn, fallback, label: fn())

    sent = []
    runner = lambda q: {"results": [{"titles": ["Already alerted"], "confidence": "HIGH"},
                                    {"titles": ["Brand new"], "confidence": "HIGH", "sources": ["reuters.com"], "verdict": "VERIFIED ✅"},
                                    {"titles": ["Low one"], "confidence": "LOW"}]}
    rep = wl.run_once(send=lambda text: sent.append(text) or True, runner=runner)
    assert rep == {"status": "ok", "watches": 1, "alerts": 1, "errors": []}
    assert "Brand new" in sent[0] and "Already alerted" not in sent[0]
    assert updates[0]["last_new"] == 1 and wl.story_key({"titles": ["Brand new"]}) in updates[0]["seen_keys"]

    # second run: nothing new → no alert
    docs[0]["seen_keys"] = updates[0]["seen_keys"]
    rep2 = wl.run_once(send=lambda text: sent.append(text) or True, runner=runner)
    assert rep2["alerts"] == 0 and len(sent) == 1


def test_run_once_isolates_failing_query(monkeypatch):
    class FakeColl:
        def find(self): return [{"_id": 1, "query": "a", "seen_keys": []}, {"_id": 2, "query": "b", "seen_keys": []}]
        def update_one(self, *a, **k): pass
    monkeypatch.setattr(wl, "watchlist_collection", FakeColl())
    monkeypatch.setattr(wl, "_safe", lambda fn, fallback, label: fn())
    def runner(q):
        if q == "a": raise RuntimeError("tavily down")
        return {"results": []}
    rep = wl.run_once(send=lambda t: True, runner=runner)
    assert rep["watches"] == 2 and rep["errors"] == ["a: RuntimeError"] and rep["alerts"] == 0


# ── telegram ────────────────────────────────────────────────────────────────
def test_format_alert_escapes_html_and_caps_at_five():
    stories = [{"titles": [f"<b>Story {i}</b>"], "sources": ["reuters.com"], "verdict": "VERIFIED ✅",
                "articles": [{"url": "https://x/y"}]} for i in range(7)]
    text = telegram.format_alert("iran & iraq", stories, "https://site/app")
    assert "&lt;b&gt;Story 0&lt;/b&gt;" in text and "iran &amp; iraq" in text
    assert "…and 2 more" in text and text.count("• ") == 5 and text.endswith("https://site/app")


def test_send_message_unconfigured_returns_false(monkeypatch):
    monkeypatch.setattr(telegram, "TELEGRAM_BOT_TOKEN", "")
    assert telegram.send_message("x") is False


# ── /news route through the service (all external calls mocked) ─────────────
def test_news_route_uses_service_and_returns_geo(monkeypatch):
    from fastapi.testclient import TestClient
    import api.routes.news as news_route
    import api.main as main
    fake = {"status": "verified", "fresh": True, "query": "q", "total_articles": 2, "total_stories": 1,
            "contradictions": [], "results": [{"titles": ["t"], "confidence": "HIGH", "geo": {"country": "Iran", "lat": 32.4, "lng": 53.7}}]}
    monkeypatch.setattr(news_route, "run_news_query", lambda q, cache_hours=1: fake)
    c = TestClient(main.app)
    r = c.post("/api/v1/news", json={"query": "q"})
    assert r.status_code == 200 and r.json()["results"][0]["geo"]["country"] == "Iran"

    def none(q, cache_hours=1): raise news_route.NoArticles(q)
    monkeypatch.setattr(news_route, "run_news_query", none)
    assert c.post("/api/v1/news", json={"query": "q"}).status_code == 404


def test_watchlist_routes(monkeypatch):
    from fastapi.testclient import TestClient
    import api.routes.news as news_route
    import api.main as main
    store = {}
    monkeypatch.setattr(news_route.wl, "add_watch", lambda q: store.setdefault(q.lower(), q) and {"status": "added", "query": q})
    monkeypatch.setattr(news_route.wl, "list_watches", lambda: [{"query": q, "last_run": None, "seen_count": 0} for q in store.values()])
    monkeypatch.setattr(news_route.wl, "remove_watch", lambda q: store.pop(q.lower(), None) is not None)
    c = TestClient(main.app)
    assert c.post("/api/v1/watchlist", json={"query": "Iran"}).json()["status"] == "added"
    assert c.get("/api/v1/watchlist").json()["watches"][0]["query"] == "Iran"
    assert c.delete("/api/v1/watchlist", params={"query": "iran"}).status_code == 200
    assert c.delete("/api/v1/watchlist", params={"query": "iran"}).status_code == 404
    assert c.post("/api/v1/watchlist/test-alert").status_code == 503   # telegram not configured in tests
