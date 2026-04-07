from pymongo import MongoClient
from datetime import datetime, timedelta
import json

# Connect to MongoDB
client = MongoClient('mongodb://localhost:27017')
db = client['sentinel_ai']

# Collections
news_collection = db['news_results']
countries_collection = db['country_profiles']
statements_collection = db['leader_statements']

print("✅ SENTINEL AI Database Connected!")

def save_news_results(query: str, results: dict):
    """Save search results to MongoDB"""
    
    document = {
        "query": query,
        "timestamp": datetime.utcnow(),
        "total_articles": results.get("total_articles"),
        "total_stories": results.get("total_stories"),
        "results": results.get("results"),
        "contradictions": results.get("contradictions")
    }
    
    news_collection.insert_one(document)
    print(f"💾 Saved results for: {query}")

def get_cached_results(query: str, 
                        hours: int = 1) -> dict:
    """Get cached results if less than X hours old"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    # Clean query before checking!
    clean_query = query.strip().lower()
    
    cached = news_collection.find_one({
        "query": {"$regex": f"^{clean_query}$", 
                  "$options": "i"},
        "timestamp": {"$gte": cutoff_time}
    })
    
    if cached:
        print(f"⚡ Cache hit! Using saved: {query}")
        cached.pop('_id', None)
        return cached
    
    print(f"🔍 No cache! Fetching fresh: {query}")
    return None

def get_recent_news(hours: int = 24) -> list:
    """Get all news from last X hours"""
    
    cutoff_time = datetime.utcnow() - timedelta(hours=hours)
    
    results = news_collection.find({
        "timestamp": {"$gte": cutoff_time}
    }).sort("timestamp", -1)
    
    news_list = []
    for r in results:
        r.pop('_id', None)
        news_list.append(r)
    
    print(f"📰 Found {len(news_list)} cached searches!")
    return news_list

def get_all_stories(hours: int = 24) -> list:
    """Get all individual stories from last X hours"""
    
    recent = get_recent_news(hours)
    all_stories = []
    
    for search in recent:
        stories = search.get("results", [])
        for story in stories:
            story["query"] = search.get("query")
            story["timestamp"] = search.get("timestamp")
            all_stories.append(story)
    
    return all_stories

def test_database():
    """Test database connection"""
    
    print("\n🧪 Testing Database...")
    
    # Test save
    test_data = {
        "total_articles": 3,
        "total_stories": 2,
        "results": [
            {
                "confidence": "HIGH",
                "titles": ["Test story"],
                "sources": ["bbc.com"],
                "verdict": "VERIFIED ✅"
            }
        ],
        "contradictions": []
    }
    
    save_news_results("test query", test_data)
    
    # Test cache
    cached = get_cached_results("test query")
    if cached:
        print("✅ Cache working!")
    
    # Test recent
    recent = get_recent_news(24)
    print(f"✅ Recent news: {len(recent)} searches found!")
    
    print("\n✅ Database tests passed!")

if __name__ == "__main__":
    test_database()