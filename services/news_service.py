"""
The news pipeline as a plain function, so the /news route, /news/stream and the watchlist
scheduler run exactly the same code: cache → collect → verify → enrich (claims ∥ entities ∥ geotag) → save.

`on_stage(name, detail)` is an optional callback (used by the SSE endpoint to stream progress).
The three enrichment steps are independent LLM calls, so they run concurrently in a small thread
pool: a fresh search costs the latency of the slowest one instead of the sum.
"""
import time
from concurrent.futures import ThreadPoolExecutor

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


def enrich(stories: list, stage=_noop) -> None:
    """claims ∥ entities ∥ geotag — each fail-soft, each reports its own stage when it starts/ends."""
    jobs = []
    if CLAIMS_ENABLED:
        jobs.append(("claims", extract_claims))
    else:
        for s in stories:
            s.setdefault("claims", [])
    if ENTITIES_ENABLED:
        jobs.append(("entities", extract_entities))
    else:
        for s in stories:
            s.setdefault("entities", [])
    jobs.append(("geotag", geotag_stories))

    def run(job):
        name, fn = job
        stage(name, "running in parallel")
        t0 = time.time()
        fn(stories)          # every fn mutates stories in place and never raises
        stage(name, f"done in {time.time() - t0:.1f}s")

    with ThreadPoolExecutor(max_workers=len(jobs)) as pool:
        list(pool.map(run, jobs))


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

    enrich(stories, stage)

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
