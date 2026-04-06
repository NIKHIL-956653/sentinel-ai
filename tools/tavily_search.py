from tavily import TavilyClient
from config import (
    TAVILY_API_KEY,
    TAVILY_MAX_RESULTS,
    TAVILY_SEARCH_DEPTH,
    TAVILY_INCLUDE_DOMAINS
)

client = TavilyClient(api_key=TAVILY_API_KEY)

def search_military_news(query: str) -> list:
    """Search for military/geopolitical news"""
    
    print(f"🔍 Searching: {query}")
    
    response = client.search(
        query=query,
        search_depth=TAVILY_SEARCH_DEPTH,
        max_results=TAVILY_MAX_RESULTS,
        include_domains=TAVILY_INCLUDE_DOMAINS
    )
    
    articles = []
    for result in response.get("results", []):
        articles.append({
            "title": result.get("title"),
            "url": result.get("url"),
            "content": result.get("content"),
            "source": result.get("url", "").split("/")[2],
            "score": result.get("score")
        })
    
    print(f"✅ Found {len(articles)} articles!")
    return articles


def test_search():
    """Quick test function"""
    results = search_military_news(
        "latest military news Middle East 2025"
    )
    for r in results:
        print(f"\n📰 {r['title']}")
        print(f"🌐 {r['source']}")
        print(f"🔗 {r['url']}")

if __name__ == "__main__":
    test_search()