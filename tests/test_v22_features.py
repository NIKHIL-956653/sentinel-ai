"""SENTINEL 2.2: claims, entities, graph, timeline, brief, metrics, SSE stream, exports, Redis limiter."""
import json

import pytest
from fastapi.testclient import TestClient

from tools import claims, entities
from services import graph as graph_svc
from services import timeline as tl_svc
from services import brief as brief_svc
from api import metrics
from api.security import RedisSlidingWindowLimiter, SlidingWindowLimiter
from tools.llm import LLMError
from tools.report import news_markdown, country_markdown


def story(title, conf="HIGH", **kw):
    return {"titles": [title], "confidence": conf, "sources": ["reuters.com"], "articles": [{"url": "https://x/" + title[:5], "content": "c"}], **kw}


# ── claims ──────────────────────────────────────────────────────────────────
def test_parse_claims_validates_indices_and_statuses():
    raw = [
        {"story": 0, "claims": [{"text": "A entered B", "supported_by": [1, 0, 9, "x"], "contradicted_by": []},
                                {"text": "12 killed", "supported_by": [], "contradicted_by": [2]},
                                {"text": "", "supported_by": [1]}, "junk",
                                {"text": "fourth", "supported_by": []}, {"text": "fifth", "supported_by": []}]},
        {"story": "nope"}, {"story": 7, "claims": []}, {"story": 1, "claims": "not a list"},
    ]
    out = claims.parse_claims(raw, 3)
    assert list(out) == [0]
    assert [c["status"] for c in out[0]] == ["corroborated", "disputed", "single-source"]
    assert out[0][0]["supported_by"] == [1]          # self-ref 0, out-of-range 9 and junk dropped
    assert len(out[0]) == claims.MAX_CLAIMS_PER_STORY
    assert claims.parse_claims({"not": "a list"}, 3) == {}


def test_extract_claims_is_fail_soft_and_summarises(monkeypatch):
    def fail(*a, **k): raise LLMError("down")
    monkeypatch.setattr(claims, "chat_json", fail)
    s = [story("a"), story("b")]
    claims.extract_claims(s)
    assert s[0]["claims"] == [] and claims.claim_summary(s) == {"total": 0, "corroborated": 0, "disputed": 0, "single_source": 0}

    monkeypatch.setattr(claims, "chat_json", lambda *a, **k: [{"story": 1, "claims": [{"text": "x", "supported_by": [0]}]}])
    claims.extract_claims(s)
    assert s[1]["claims"][0]["status"] == "corroborated"
    assert claims.claim_summary(s)["corroborated"] == 1


# ── entities ────────────────────────────────────────────────────────────────
def test_parse_entities_normalises_types_and_dedupes():
    raw = [{"story": 0, "entities": [{"name": "U.S. Navy", "type": "org"}, {"name": "US Navy", "type": "organisation"},
                                     {"name": "Putin", "type": "leader"}, {"name": "S-400", "type": "system"},
                                     {"name": "Mars", "type": "planet"}, {"name": "", "type": "place"}]}]
    out = entities.parse_entities(raw, 1)
    assert [(e["name"], e["type"]) for e in out[0]] == [("U.S. Navy", "organisation"), ("Putin", "person"), ("S-400", "weapon")]
    assert entities.canonical("U.S. Navy") == entities.canonical("us navy")


def test_extract_entities_fail_soft(monkeypatch):
    def fail(*a, **k): raise LLMError("down")
    monkeypatch.setattr(entities, "chat_json", fail)
    s = [story("a")]
    entities.extract_entities(s)
    assert s[0]["entities"] == []


# ── graph ───────────────────────────────────────────────────────────────────
def test_build_graph_links_stories_entities_countries_and_leaders():
    stories = [
        story("Northland enters Karim", geo={"country": "Ukraine", "lat": 1.0, "lng": 2.0}, query="q1",
              entities=[{"name": "Vladimir Putin", "type": "person"}, {"name": "Russia", "type": "place"}, {"name": "S-400", "type": "weapon"}]),
        story("Second", query="q2", entities=[{"name": "russia", "type": "place"}, {"name": "Vladimir Putin", "type": "person"}]),
        {"no_titles": True},
    ]
    g = graph_svc.build_graph(stories)
    types = {n["id"]: n for n in g["nodes"]}
    assert g["stats"]["stories"] == 2
    assert "place:ukraine" in types and types["place:ukraine"]["country"] is True
    assert "place:russia" in types and types["place:russia"]["degree"] == 2          # merged across spelling
    assert any(e["rel"] == "leads" and e["from"] == "person:vladimir putin" and e["to"] == "place:russia" for e in g["edges"])
    assert sum(1 for e in g["edges"] if e["rel"] == "located") == 1
    # query filter
    assert graph_svc.build_graph(stories, query="Q2")["stats"]["stories"] == 1


# ── timeline ────────────────────────────────────────────────────────────────
def test_build_timeline_tracks_story_across_runs():
    from datetime import datetime
    runs = [
        {"timestamp": datetime(2026, 1, 1), "results": [story("Karim falls", "LOW", verdict="UNVERIFIED ⚠️")], "contradictions": []},
        {"timestamp": datetime(2026, 1, 2), "results": [story("Karim falls", "HIGH", verdict="VERIFIED ✅", claims=[{"status": "disputed"}]),
                                                        story("New thing", "MEDIUM")], "contradictions": [{}]},
        "junk",
    ]
    tl = tl_svc.build_timeline(runs)
    assert len(tl["runs"]) == 2 and tl["runs"][1]["contradictions"] == 1 and tl["runs"][1]["high"] == 1
    karim = next(s for s in tl["stories"] if s["title"] == "Karim falls")
    assert karim["trend"] == "up" and karim["runs_seen"] == 2
    assert karim["cells"][0]["confidence"] == "LOW" and karim["cells"][1]["disputed_claims"] == 1
    new = next(s for s in tl["stories"] if s["title"] == "New thing")
    assert new["cells"][0] is None and new["first_run"] == 1 and new["trend"] == "flat"
    assert tl["stories"][0]["title"] == "Karim falls"       # most-seen first


# ── brief ───────────────────────────────────────────────────────────────────
@pytest.fixture
def brief_inputs(monkeypatch):
    stories = [story("Northland enters Karim", geo={"country": "Ukraine"}, query="q", verdict="VERIFIED ✅",
                     claims=[{"text": "12 killed", "status": "disputed"}]),
               story("Northland enters Karim", query="q"),      # duplicate headline → deduped
               story("Budget passes", "LOW", query="q2", verdict="DISPUTED ❌")]
    monkeypatch.setattr(brief_svc, "get_all_stories", lambda hours: list(stories))
    import database
    monkeypatch.setattr(database, "get_recent_news", lambda hours: [{"query": "q", "contradictions": [{"story1": "a", "story2": "b", "conflict": "x"}]},
                                                                      {"query": "q2", "contradictions": [{"story1": "a", "story2": "b", "conflict": "x"}]}])
    monkeypatch.setattr(brief_svc, "get_cached_statements", lambda hours: [{"leader": "L", "sentiment": "warning", "statement": "s"}])
    monkeypatch.setattr(brief_svc, "get_cached_brief", lambda hours: None)
    saved = []
    monkeypatch.setattr(brief_svc, "save_brief", lambda b: saved.append(b))
    return saved


def test_gather_inputs_dedupes_and_counts(brief_inputs):
    inp = brief_svc.gather_inputs(24)
    assert inp["counts"] == {"stories": 2, "high": 1, "verified": 1, "disputed": 1, "contradictions": 1, "sources": 1}
    assert inp["regions"] == [("Ukraine", 1)] and inp["disputed_claims"][0]["claim"] == "12 killed"


def test_build_brief_uses_llm_sections_and_saves(brief_inputs):
    llm = lambda prompt, max_tokens=0: {"headline": "H", "assessment": "A", "top_developments": ["one [0]", "", 3],
                                        "contradictions": [], "watch_items": "not a list"}
    b = brief_svc.build_brief(24, llm=llm, force=True)
    assert b["sections"]["headline"] == "H" and b["sections"]["top_developments"] == ["one [0]", "3"]
    assert b["sections"]["watch_items"] == [] and b["sections"]["llm"] is True and b["model"]
    assert brief_inputs and brief_inputs[0]["counts"]["stories"] == 2
    md = brief_svc.to_markdown(b)
    assert md.startswith("# SENTINEL Intelligence Brief") and "## Top developments" in md and "[0] Northland enters Karim" in md
    tg = brief_svc.to_telegram(b)
    assert "<b>H</b>" in tg and "• one [0]" in tg


def test_build_brief_falls_back_when_llm_fails(brief_inputs):
    def fail(prompt, max_tokens=0): raise LLMError("down")
    b = brief_svc.build_brief(24, llm=fail, force=True)
    assert b["sections"]["llm"] is False and b["model"] is None
    assert "LLM summary unavailable" in b["sections"]["headline"]
    assert "_LLM summary unavailable" in brief_svc.to_markdown(b)
    # junk shape from the model is also a fallback, not a crash
    b2 = brief_svc.build_brief(24, llm=lambda p, max_tokens=0: ["list"], force=True)
    assert b2["sections"]["llm"] is False


def test_send_brief_injectable(brief_inputs, monkeypatch):
    monkeypatch.setattr(brief_svc, "chat_json", lambda p, max_tokens=0: {"headline": "H", "assessment": "A"})
    sent = []
    r = brief_svc.send_brief(send=lambda t: sent.append(t) or True, force=True)
    assert r["sent"] is True and sent and "SENTINEL BRIEF" in sent[0]


# ── metrics ─────────────────────────────────────────────────────────────────
def test_metrics_counters_and_prometheus_text():
    metrics.reset()
    metrics.record_request("/api/v1/country/India", 200, 0.3)
    metrics.record_request("/api/v1/country/Iran", 500, 2.0)
    metrics.record_llm(prompt_tokens=1000, completion_tokens=500, seconds=1.0, cost=0.01)
    metrics.record_llm(prompt_tokens=1_000_000, completion_tokens=0, seconds=1.0, cost=None)   # estimated
    metrics.record_llm(seconds=0.1, ok=False)
    metrics.record_search(cache_hit=True); metrics.record_search(cache_hit=False, stories=4, contradictions=1)
    s = metrics.snapshot()
    r = s["routes"]["/api/v1/country/{param}"]
    assert r["count"] == 2 and r["errors_5xx"] == 1 and r["max_ms"] == 2000
    assert s["llm"]["calls"] == 3 and s["llm"]["errors"] == 1 and s["llm"]["cost_is_estimate"] is True
    assert abs(s["llm"]["cost_usd"] - (0.01 + metrics.LLM_PRICE_IN_PER_M)) < 1e-6
    assert s["pipeline"] == {"searches": 2, "cache_hits": 1, "stories": 4, "contradictions": 1}
    text = metrics.prometheus_text()
    assert 'sentinel_http_requests_total{route="/api/v1/country/{param}",status="500"} 1' in text
    assert "sentinel_llm_tokens_total{kind=\"prompt\"} 1001000" in text
    assert 'sentinel_searches_total{result="cache_hit"} 1' in text
    metrics.reset()


def test_llm_chat_records_usage(monkeypatch):
    import tools.llm as llm
    metrics.reset()
    class R:
        status_code = 200
        text = ""
        def json(self): return {"choices": [{"message": {"content": "hi"}}], "usage": {"prompt_tokens": 10, "completion_tokens": 5, "cost": 0.002}}
    monkeypatch.setattr(llm.requests, "post", lambda *a, **k: R())
    assert llm.chat("p") == "hi"
    s = metrics.snapshot()["llm"]
    assert s["calls"] == 1 and s["prompt_tokens"] == 10 and abs(s["cost_usd"] - 0.002) < 1e-9 and s["cost_is_estimate"] is False
    metrics.reset()


# ── Redis-backed limiter (fake client) ──────────────────────────────────────
class FakePipe:
    def __init__(self, store, now_box): self.store, self.ops, self.now_box = store, [], now_box
    def zremrangebyscore(self, k, lo, hi): self.ops.append(("zrem", k, hi)); return self
    def zcard(self, k): self.ops.append(("zcard", k)); return self
    def zrange(self, k, a, b, withscores=False): self.ops.append(("zrange", k)); return self
    def zadd(self, k, mapping): self.ops.append(("zadd", k, list(mapping.values())[0])); return self
    def expire(self, k, s): return self
    def execute(self):
        out = []
        for op in self.ops:
            z = self.store.setdefault(op[1], [])
            if op[0] == "zrem": z[:] = [t for t in z if t > op[2]]; out.append(0)
            elif op[0] == "zcard": out.append(len(z))
            elif op[0] == "zrange": out.append([("m", z[0])] if z else [])
            elif op[0] == "zadd": z.append(op[2]); z.sort(); out.append(1)
        return out


class FakeRedis:
    def __init__(self): self.store = {}; self.broken = False
    def pipeline(self):
        if self.broken: raise ConnectionError("redis down")
        return FakePipe(self.store, None)


def test_redis_limiter_shares_window_and_falls_back():
    r = FakeRedis()
    lim = RedisSlidingWindowLimiter(r, limit=2, window=60)
    assert lim.check("ip", now=0)[0] and lim.check("ip", now=1)[0]
    allowed, retry = lim.check("ip", now=2)
    assert not allowed and 57 <= retry <= 59
    assert lim.check("ip", now=61)[0]                     # oldest expired
    other = RedisSlidingWindowLimiter(r, limit=2, window=60)   # "second instance", same store
    assert other.check("ip", now=62)[0] and not other.check("ip", now=63)[0]
    r.broken = True
    assert lim.check("new-ip")[0]                          # degraded to in-memory, never blocks


def test_memory_limiter_unchanged():
    lim = SlidingWindowLimiter(limit=1, window=10)
    assert lim.check("a", now=0)[0] and not lim.check("a", now=1)[0]


# ── routes: SSE stream, timeline, graph, brief, export, stats, metrics ───────
@pytest.fixture
def client(monkeypatch):
    import api.routes.news as news_route
    import api.security as sec
    sec.general_limiter.reset(); sec.expensive_limiter.reset()
    monkeypatch.setattr(sec.expensive_limiter, "limit", 100)
    import api.main as main
    return TestClient(main.app), news_route


def test_news_stream_emits_stages_then_result(client, monkeypatch):
    c, news_route = client
    def fake_run(query, cache_hours=1, on_stage=None):
        on_stage("collect", "x"); on_stage("done", "ok")
        return {"status": "verified", "fresh": True, "query": query, "total_articles": 1, "total_stories": 1,
                "contradictions": [], "results": [{"titles": ["t"], "confidence": "HIGH"}], "claim_summary": {}}
    monkeypatch.setattr(news_route, "run_news_query", fake_run)
    with c.stream("POST", "/api/v1/news/stream", json={"query": "q"}) as r:
        assert r.status_code == 200 and r.headers["content-type"].startswith("text/event-stream")
        body = "".join(r.iter_text())
    events = [blk.split("\n")[0].replace("event: ", "") for blk in body.strip().split("\n\n")]
    assert events == ["stages", "stage", "stage", "result"]
    result = json.loads(body.strip().split("\n\n")[-1].split("\n")[1][5:])
    assert result["results"][0]["titles"] == ["t"] and result["fresh"] is True

    def none(query, cache_hours=1, on_stage=None): raise news_route.NoArticles(query)
    monkeypatch.setattr(news_route, "run_news_query", none)
    with c.stream("POST", "/api/v1/news/stream", json={"query": "q"}) as r:
        body = "".join(r.iter_text())
    assert "event: error" in body and '"status": 404' in body


def test_timeline_graph_brief_export_routes(client, monkeypatch):
    c, news_route = client
    from datetime import datetime
    run = {"query": "q", "timestamp": datetime(2026, 1, 1), "total_articles": 1, "total_stories": 1, "contradictions": [],
           "results": [story("Karim falls", geo={"country": "Ukraine", "lat": 1.0, "lng": 2.0}, query="q",
                             entities=[{"name": "S-400", "type": "weapon"}], claims=[{"text": "x", "status": "corroborated", "supported_by": [0], "contradicted_by": []}])]}
    monkeypatch.setattr(tl_svc, "get_query_history", lambda q, days=7: [run, run])
    monkeypatch.setattr(news_route, "get_all_stories", lambda hours: list(run["results"]))
    monkeypatch.setattr(news_route, "get_cached_results", lambda q, hours=1: run if q == "q" else None)
    monkeypatch.setattr(news_route, "get_recent_queries", lambda hours=1: [{"query": "q", "runs": 2, "last": None}])
    monkeypatch.setattr(brief_svc, "build_brief", lambda hours, llm, force: {"generated_at": "2026-01-01T00:00:00Z", "window_hours": 24, "model": None,
                                                                            "counts": {"stories": 1, "sources": 1, "verified": 1, "disputed": 0, "contradictions": 0},
                                                                            "regions": [], "queries": [], "disputed_claims": [], "stories": [],
                                                                            "sections": {"headline": "H", "assessment": "A", "llm": False}})

    tl = c.get("/api/v1/news/timeline", params={"q": "q", "days": 7}).json()
    assert len(tl["runs"]) == 2 and tl["stories"][0]["runs_seen"] == 2
    assert c.get("/api/v1/news/timeline").status_code == 422          # q required
    assert c.get("/api/v1/news/queries").json()["queries"][0]["runs"] == 2

    g = c.get("/api/v1/graph", params={"hours": 24}).json()
    assert g["stats"]["stories"] == 1 and any(n["id"] == "weapon:s 400" for n in g["nodes"])

    b = c.get("/api/v1/brief").json()
    assert b["sections"]["headline"] == "H"
    md = c.get("/api/v1/brief", params={"format": "md"})
    assert md.headers["content-type"].startswith("text/markdown") and "# SENTINEL Intelligence Brief" in md.text
    assert c.post("/api/v1/brief/send").status_code == 503             # telegram not configured in tests

    ex = c.get("/api/v1/export/news", params={"q": "q", "format": "md"})
    assert ex.status_code == 200 and "attachment" in ex.headers["content-disposition"] and "✅ corroborated" in ex.text
    assert c.get("/api/v1/export/news", params={"q": "q", "format": "json"}).json()["query"] == "q"
    assert c.get("/api/v1/export/news", params={"q": "nope"}).status_code == 404

    st = c.get("/api/v1/stats").json()
    assert "llm" in st and "routes" in st
    m = c.get("/metrics")
    assert m.status_code == 200 and "sentinel_http_requests_total" in m.text
    assert c.get("/api/v1/health").json()["rate_limiter"] == "memory"
    assert "news_stream" in c.get("/").json()["endpoints"]


def test_country_export_markdown(client, monkeypatch):
    c, _ = client
    import api.routes.country as cr
    monkeypatch.setattr(cr, "_load_profile", lambda name: {"country": name, "military_summary": "S", "army_strength": "1",
                                                           "key_weapons": ["X"], "expenditure_series": [{"year": 2020, "value": 1e9}],
                                                           "data_source": "test"})
    r = c.get("/api/v1/export/country/India")
    assert r.status_code == 200 and "# India — military dossier" in r.text and "| 2020 | 1,000,000,000 |" in r.text
    assert c.get("/api/v1/export/country/India", params={"format": "json"}).json()["country"] == "India"


def test_report_generators_pure():
    md = news_markdown({"query": "q", "total_articles": 2, "contradictions": [{"conflict": "c", "story1": "a", "story2": "b", "method": "llm"}],
                        "results": [story("T", trust={"trusted": ["reuters.com"], "unknown": [], "unreliable": []}, verdict="VERIFIED ✅",
                                          entities=[{"name": "E", "type": "weapon"}])]})
    assert "**c** (llm judge)" in md and "- Entities: E (weapon)" in md
    assert "## Key weapons" not in country_markdown({"country": "X"})


# ── pipeline wiring: stages + claims/entities attached, fail-soft ───────────
def test_run_news_query_reports_stages_and_attaches_claims(monkeypatch):
    import services.news_service as ns
    monkeypatch.setattr(ns, "get_cached_results", lambda q, hours=1: None)
    saved = {}
    monkeypatch.setattr(ns, "save_news_results", lambda q, r: saved.update(r))
    monkeypatch.setattr(ns._collector, "collect", lambda q: {"status": "success", "query": q, "total_articles": 2, "total_stories": 1,
                                                             "results": [story("T", sources=["reuters.com", "bbc.com"])]})
    monkeypatch.setattr(ns._verifier, "check_contradictions", lambda results: [])
    monkeypatch.setattr(ns, "extract_claims", lambda s: [x.__setitem__("claims", [{"text": "c", "status": "single-source", "supported_by": [], "contradicted_by": []}]) for x in s])
    monkeypatch.setattr(ns, "extract_entities", lambda s: [x.__setitem__("entities", [{"name": "E", "type": "place"}]) for x in s])
    monkeypatch.setattr(ns, "geotag_stories", lambda s: s)
    stages = []
    out = ns.run_news_query("q", on_stage=lambda n, d="": stages.append(n))
    assert stages[0] == "cache" and stages[-1] == "done" and "claims" in stages and "entities" in stages
    assert out["results"][0]["claims"][0]["text"] == "c" and out["claim_summary"]["single_source"] == 1
    assert saved["results"][0]["entities"][0]["name"] == "E"
