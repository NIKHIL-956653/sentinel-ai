from tools.tavily_search import search_military_news
from tools.confidence_scorer import verify_news

def main():
    print("🕵️ SENTINEL AI - Starting...")
    print("="*50)
    
    # Step 1: Search news
    articles = search_military_news(
        "latest military news Middle East 2026"
    )
    
    # Step 2: Verify news
    verified = verify_news(articles)
    
    print("\n" + "="*50)
    print("✅ SENTINEL AI - Analysis Complete!")

if __name__ == "__main__":
    main()