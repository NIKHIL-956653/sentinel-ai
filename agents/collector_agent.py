from tools.tavily_search import search_military_news
from tools.confidence_scorer import verify_news

class CollectorAgent:
    """
    SENTINEL AI - News Collector Agent
    Collects and verifies military/geopolitical news
    """
    
    def __init__(self):
        self.name = "Collector Agent"
        self.role = "Military News Collector"
        print(f"🕵️ {self.name} initialized!")
    
    def collect(self, query: str) -> dict:
        """
        Main collection function
        1. Search news
        2. Verify news
        3. Return clean results
        """
        
        print(f"\n{'='*50}")
        print(f"🎯 MISSION: {query}")
        print(f"{'='*50}")
        
        # Step 1: Search
        print("\n📡 Step 1: Collecting intel...")
        articles = search_military_news(query)
        
        if not articles:
            return {
                "status": "failed",
                "query": query,
                "message": "No articles found!",
                "results": []
            }
        
        # Step 2: Verify
        print("\n🔍 Step 2: Verifying intel...")
        verified = verify_news(articles)
        
        # Step 3: Package results
        print("\n📦 Step 3: Packaging intel...")
        high = [r for r in verified 
                if r["confidence"] == "HIGH"]
        medium = [r for r in verified 
                  if r["confidence"] == "MEDIUM"]
        low = [r for r in verified 
               if r["confidence"] == "LOW"]
        
        results = {
            "status": "success",
            "query": query,
            "total_articles": len(articles),
            "total_stories": len(verified),
            "summary": {
                "high_confidence": len(high),
                "medium_confidence": len(medium),
                "low_confidence": len(low)
            },
            "results": verified
        }
        
        # Step 4: Mission report
        print(f"\n{'='*50}")
        print(f"📊 MISSION REPORT:")
        print(f"✅ HIGH confidence stories:   {len(high)}")
        print(f"⚠️  MEDIUM confidence stories: {len(medium)}")
        print(f"🔴 LOW confidence stories:    {len(low)}")
        print(f"{'='*50}")
        
        return results


def test_collector():
    """Test the collector agent"""
    agent = CollectorAgent()
    
    results = agent.collect(
        "Russia Ukraine war latest 2026"
    )
    
    print(f"\n🎯 Status: {results['status']}")
    print(f"📰 Total articles: {results['total_articles']}")
    print(f"📊 Total stories: {results['total_stories']}")


if __name__ == "__main__":
    test_collector()