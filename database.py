"""
MongoDB layer for SENTINEL AI.

Design:
- Connection string comes from config.MONGODB_URI (env MONGODB_URI) so the same
  code runs against local Mongo and Atlas.
- pymongo connects lazily; serverSelectionTimeoutMS keeps a missing Mongo from
  hanging every request for 30s.
- Every helper is fail-soft: if Mongo is down the API still answers, it just
  skips caching (and says so once in the log).
"""
import re
from datetime import datetime, timedelta

from pymongo import MongoClient
from pymongo.errors import PyMongoError

from config import MONGODB_URI, MONGODB_DB

client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=3000)
db = client[MONGODB_DB]

# Collections
news_collection = db["news_results"]          # cached searches (1h TTL, see config)
countries_collection = db["country_profiles"] # country dossiers
statements_collection = db["leader_statements"]  # leader quotes (24h TTL)
weapons_collection = db["weapons_detail_cache"]
forces_collection = db["special_forces"]

_warned = False


def get_db():
    """Shared database handle for tools that cache LLM output."""
    return db


def mongo_available() -> bool:
    """Cheap liveness check (used by /health)."""
    try:
        client.admin.command("ping")
        return True
    except PyMongoError:
        return False


def _safe(fn, fallback, label: str):
    """Run a Mongo operation; on connection failure log once and return fallback."""
    global _warned
    try:
        return fn()
    except PyMongoError as e:
        if not _warned:
            print(f"⚠️  MongoDB unavailable at {MONGODB_URI} — caching disabled ({e.__class__.__name__})")
            _warned = True
        else:
            print(f"⚠️  MongoDB skipped: {label}")
        return fallback


def _strip_id(doc):
    if doc:
        doc.pop("_id", None)
    return doc


# ── News ────────────────────────────────────────────────────────────────────
def save_news_results(query: str, results: dict) -> None:
    document = {
        "query": query,
        "query_norm": query.strip().lower(),
        "timestamp": datetime.utcnow(),
        "total_articles": results.get("total_articles"),
        "total_stories": results.get("total_stories"),
        "results": results.get("results"),
        "contradictions": results.get("contradictions"),
    }
    _safe(lambda: news_collection.insert_one(document), None, "save_news_results")
    print(f"💾 Saved results for: {query}")


def get_cached_results(query: str, hours: int = 1):
    """Return a cached search younger than `hours`, or None."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    clean = query.strip().lower()

    def _find():
        # query_norm is exact; the regex branch (escaped) matches docs saved before query_norm existed
        return news_collection.find_one({
            "$or": [
                {"query_norm": clean},
                {"query": {"$regex": f"^{re.escape(clean)}$", "$options": "i"}},
            ],
            "timestamp": {"$gte": cutoff},
        })

    cached = _safe(_find, None, "get_cached_results")
    if cached:
        print(f"⚡ Cache hit: {query}")
        return _strip_id(cached)
    print(f"🔍 No cache, fetching fresh: {query}")
    return None


def get_recent_news(hours: int = 24) -> list:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    docs = _safe(
        lambda: list(news_collection.find({"timestamp": {"$gte": cutoff}}).sort("timestamp", -1)),
        [], "get_recent_news")
    return [_strip_id(d) for d in docs]


def get_all_stories(hours: int = 24) -> list:
    stories = []
    for search in get_recent_news(hours):
        for story in search.get("results", []) or []:
            story["query"] = search.get("query")
            story["timestamp"] = search.get("timestamp")
            stories.append(story)
    return stories


# ── Country profiles ────────────────────────────────────────────────────────
def get_cached_country(country: str):
    doc = _safe(lambda: countries_collection.find_one({"country_key": country.strip().lower()}),
                None, "get_cached_country")
    return _strip_id(doc)["profile"] if doc else None


def save_country_profile(country: str, profile: dict) -> None:
    key = country.strip().lower()
    _safe(lambda: countries_collection.replace_one(
        {"country_key": key},
        {"country_key": key, "country": country, "timestamp": datetime.utcnow(), "profile": profile},
        upsert=True), None, "save_country_profile")


# ── Leader statements ───────────────────────────────────────────────────────
def get_cached_statements(hours: int = 24):
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    doc = _safe(lambda: statements_collection.find_one({"timestamp": {"$gte": cutoff}}),
                None, "get_cached_statements")
    return doc["statements"] if doc else None


def save_statements(statements: list) -> None:
    def _replace():
        statements_collection.delete_many({})
        statements_collection.insert_one({"timestamp": datetime.utcnow(), "statements": statements})
    _safe(_replace, None, "save_statements")


# ── Generic LLM-output cache (weapons, special forces) ──────────────────────
def cache_get(collection, key: str):
    doc = _safe(lambda: collection.find_one({"key": key}), None, f"cache_get:{key}")
    return doc["data"] if doc else None


def cache_put(collection, key: str, data, **extra) -> None:
    _safe(lambda: collection.replace_one(
        {"key": key}, {"key": key, "data": data, "timestamp": datetime.utcnow(), **extra}, upsert=True),
        None, f"cache_put:{key}")


def test_database():
    print("\n🧪 Testing Database...")
    print(f"URI: {MONGODB_URI}  reachable: {mongo_available()}")
    save_news_results("test query", {"total_articles": 3, "total_stories": 2,
                                      "results": [{"confidence": "HIGH", "titles": ["Test story"],
                                                   "sources": ["bbc.com"], "verdict": "VERIFIED ✅"}],
                                      "contradictions": []})
    print("cache hit:", bool(get_cached_results("test query")))
    print("recent searches:", len(get_recent_news(24)))


if __name__ == "__main__":
    test_database()
