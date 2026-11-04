"""
The news pipeline as a plain function, so the /news route, /news/stream and the watchlist
scheduler run exactly the same code: cache → collect → verify → claims → entities → geotag → save.

`on_stage(name, detail)` is an optional callback (used by the SSE endpoint to stream progress).
"""
import time

from agents.collector_agent import CollectorAgent
from agents.verifier_agent import VerifierAgent
from config import NEWS_CACHE_HOURS, CLAIMS_ENABLED, ENTITIES_ENABLED
from database import get_cached_results, save_news_results
from tools.geotag import geotag_stories
from tools.claims import extract_claims, claim_summary
from tools.entities import extract_entities
from api import metrics

_collector = CollectorAgent()
_verifier = VerifierAgent()

STAGES = [
    ("cache", "Checking intelligence cache"),
    ("collect", "Collecting from trusted sources (Tavily)"),
    ("cluster", "Clustering articles into stories"),
    ("verify", "Scoring source trust & verdicts"),
    ("contradict", "LLM judge: contradictions"),
    ("claims", "Extracting atomic claims & corroboration"),
    ("entities", "Extracting entities for the knowledge graph"),
    ("geotag", "Geotagging stories"),
    ("save", "Saving to archive"),
]


class NoArticles(Exception):
    pass


def _noop(name: str, detail: str = "") -> None:
    pass


def run_news_query(query: str, cache_hours: int = NEWS_CACHE_HOURS, on_stage=None) -> dict:
    """Returns the /news response dict plus `fresh` (False when served from cache)."""
    stage = on_stage or _noop
    t0 = time.time()
    stage("cache", "Checking intelligence cache")
    cached = get_cached_results(query, hours=cache_hours)
    if cached:
        metrics.record_search(cache_hit=True, stories=cached.get("total_stories") or 0,
                              contradictions=len(cached.get("contradictions") or []))
        stage("done", f"Served from cache in {time.time() - t0:.1f}s")
        return {
            "status": "cached", "fresh": False, "query": cached["query"],
            "total_articles": cached["total_articles"], "total_stories": cached["total_stories"],
            "contradictions": cached["contradictions"], "results": cached["results"],
            "claim_summary": claim_summary(cached["results"] or []),
            "timestamp": cached.get("timestamp"),
        }

    stage("collect", "Collecting from trusted sources (Tavily)")
    collected = _collector.collect(query)
    if collected["status"] == "failed":
        stage("error", "No articles found")
        raise NoArticles(query)
    stage("cluster", f"{collected['total_articles']} articles → {collected['total_stories']} stories")

    stage("verify", "Scoring source trust & verdicts")
    # verify() does trust + contradictions in one go; report the judge stage before it starts
    stage("contradict", "LLM judge reading all stories for contradictions")
    verified = _verifier.verify(collected)
    stories = verified["results"]

    if CLAIMS_ENABLED:
        stage("claims", "Extracting atomic claims & cross-source corroboration")
        extract_claims(stories)
    else:
        for s in stories:
            s.setdefault("claims", [])
    if ENTITIES_ENABLED:
        stage("entities", "Extracting entities for the knowledge graph")
        extract_entities(stories)
    else:
        for s in stories:
            s.setdefault("entities", [])

    stage("geotag", "Geotagging stories for the threat map")
    geotag_stories(stories)

    stage("save", "Saving to archive")
    save_news_results(query, {
        "total_articles": collected["total_articles"],
        "total_stories": verified["total_stories"],
        "results": stories,
        "contradictions": verified["contradictions"],
    })
    metrics.record_search(cache_hit=False, stories=verified["total_stories"],
                          contradictions=len(verified["contradictions"]))
    stage("done", f"Pipeline finished in {time.time() - t0:.1f}s")
    return {
        "status": verified["status"], "fresh": True, "query": verified["query"],
        "total_articles": collected["total_articles"], "total_stories": verified["total_stories"],
        "contradictions": verified["contradictions"], "results": stories,
        "claim_summary": claim_summary(stories),
    }
