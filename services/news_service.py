"""
The news pipeline as a plain function, so the /news route and the watchlist scheduler run
exactly the same code: cache → collect → verify → geotag → save.
"""
from agents.collector_agent import CollectorAgent
from agents.verifier_agent import VerifierAgent
from config import NEWS_CACHE_HOURS
from database import get_cached_results, save_news_results
from tools.geotag import geotag_stories

_collector = CollectorAgent()
_verifier = VerifierAgent()


class NoArticles(Exception):
    pass


def run_news_query(query: str, cache_hours: int = NEWS_CACHE_HOURS) -> dict:
    """Returns the /news response dict plus `fresh` (False when served from cache)."""
    cached = get_cached_results(query, hours=cache_hours)
    if cached:
        return {
            "status": "cached", "fresh": False, "query": cached["query"],
            "total_articles": cached["total_articles"], "total_stories": cached["total_stories"],
            "contradictions": cached["contradictions"], "results": cached["results"],
        }

    collected = _collector.collect(query)
    if collected["status"] == "failed":
        raise NoArticles(query)

    verified = _verifier.verify(collected)
    geotag_stories(verified["results"])

    save_news_results(query, {
        "total_articles": collected["total_articles"],
        "total_stories": verified["total_stories"],
        "results": verified["results"],
        "contradictions": verified["contradictions"],
    })
    return {
        "status": verified["status"], "fresh": True, "query": verified["query"],
        "total_articles": collected["total_articles"], "total_stories": verified["total_stories"],
        "contradictions": verified["contradictions"], "results": verified["results"],
    }
