import pytest

import agents.verifier_agent as va
from agents.verifier_agent import VerifierAgent
from tools.llm import LLMError


def story(title, sources=("reuters.com",)):
    return {"titles": [title], "sources": list(sources), "confidence": "HIGH", "articles": []}


# ── verdict rule ────────────────────────────────────────────────────────────
@pytest.mark.parametrize("sources,conf,expected", [
    (["reuters.com", "bbc.com"], "HIGH", "VERIFIED ✅"),
    (["reuters.com", "blog.example"], "MEDIUM", "VERIFIED ✅"),
    (["reuters.com"], "LOW", "UNVERIFIED ⚠️"),
    (["blog.example"], "LOW", "UNVERIFIED ⚠️"),
    (["blogA.example", "blogB.example"], "MEDIUM", "NEEDS REVIEW 🔍"),   # unknown-only never VERIFIED
    (["rt.com"], "LOW", "DISPUTED ❌"),
    (["bbc.com", "rt.com"], "MEDIUM", "DISPUTED ❌"),
    (["bbc.com", "reuters.com", "rt.com"], "HIGH", "VERIFIED ✅"),
])
def test_verdict_rule(sources, conf, expected):
    v = VerifierAgent()
    assert v.verdict_for(v.check_source_trust(sources), conf) == expected


# ── keyword heuristic ───────────────────────────────────────────────────────
def test_keyword_contradiction_detects_opposites_and_tags_method():
    res = VerifierAgent.check_contradictions_keyword([
        story("Northland claims victory in Karim"), story("Northland admits defeat in Karim")])
    assert len(res) == 1 and res[0]["method"] == "keyword" and "victory" in res[0]["conflict"]


def test_keyword_contradiction_misses_numeric_conflict():
    # documents the known weakness the LLM judge exists for
    res = VerifierAgent.check_contradictions_keyword([
        story("12 soldiers killed in strike"), story("No casualties in strike, ministry says")])
    assert res == []


# ── LLM judge (mocked) ──────────────────────────────────────────────────────
def test_llm_contradiction_parses_and_dedupes(monkeypatch):
    monkeypatch.setattr(va, "chat_json", lambda *a, **k: [
        {"a": 0, "b": 1, "conflict": "one says ceasefire holds, other says shelling continues"},
        {"a": 1, "b": 0, "conflict": "duplicate reversed pair"},
        {"a": 0, "b": 0, "conflict": "self pair must be dropped"},
        {"a": 7, "b": 1, "conflict": "out of range must be dropped"},
        {"bogus": True},
    ])
    res = VerifierAgent.check_contradictions_llm([story("Ceasefire holds"), story("Shelling continues")])
    assert len(res) == 1
    assert res[0]["method"] == "llm" and res[0]["story1"] == "Ceasefire holds"


def test_llm_contradiction_skips_single_story_without_calling_model(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("model must not be called for < 2 stories")
    monkeypatch.setattr(va, "chat_json", boom)
    assert VerifierAgent.check_contradictions_llm([story("only one")]) == []


def test_dispatch_falls_back_to_keyword_when_llm_fails(monkeypatch):
    def fail(*a, **k):
        raise LLMError("simulated outage")
    monkeypatch.setattr(va, "chat_json", fail)
    monkeypatch.setattr(va, "CONTRADICTION_MODE", "llm")
    res = VerifierAgent().check_contradictions([story("Ceasefire announced"), story("Attack resumes")])
    assert res and res[0]["method"] == "keyword"


def test_dispatch_keyword_mode_never_calls_llm(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("LLM must not be called in keyword mode")
    monkeypatch.setattr(va, "chat_json", boom)
    monkeypatch.setattr(va, "CONTRADICTION_MODE", "keyword")
    VerifierAgent().check_contradictions([story("a b c"), story("d e f")])


def test_verify_end_to_end_adds_trust_verdict_and_contradictions(monkeypatch):
    monkeypatch.setattr(va, "chat_json", lambda *a, **k: [])
    collected = {"query": "q", "results": [story("Northland enters Karim", ["reuters.com", "bbc.com"]),
                                           story("Southmark budget passes", ["rt.com"])]}
    out = VerifierAgent().verify(collected)
    assert out["status"] == "verified" and out["total_stories"] == 2
    assert out["results"][0]["verdict"] == "VERIFIED ✅"
    assert out["results"][1]["verdict"] == "DISPUTED ❌"
    assert out["contradictions"] == []
