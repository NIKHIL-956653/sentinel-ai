from config import LEADERS_CACHE_HOURS
from tools.llm import chat_json, LLMError
from database import get_cached_statements, save_statements

# World leaders to track
TRACKED_LEADERS = {
    "United States": {"leader": "Donald Trump", "flag": "🇺🇸", "role": "President"},
    "Russia": {"leader": "Vladimir Putin", "flag": "🇷🇺", "role": "President"},
    "China": {"leader": "Xi Jinping", "flag": "🇨🇳", "role": "President"},
    "Israel": {"leader": "Benjamin Netanyahu", "flag": "🇮🇱", "role": "Prime Minister"},
    "Iran": {"leader": "Ali Khamenei", "flag": "🇮🇷", "role": "Supreme Leader"},
    "UAE": {"leader": "Mohammed bin Zayed", "flag": "🇦🇪", "role": "President"},
    "Saudi Arabia": {"leader": "Mohammed bin Salman", "flag": "🇸🇦", "role": "Crown Prince"},
    "Turkey": {"leader": "Recep Erdogan", "flag": "🇹🇷", "role": "President"},
    "Ukraine": {"leader": "Volodymyr Zelensky", "flag": "🇺🇦", "role": "President"},
    "North Korea": {"leader": "Kim Jong-un", "flag": "🇰🇵", "role": "Supreme Leader"},
}

def get_sentiment_emoji(sentiment: str) -> str:
    """Get emoji for sentiment"""
    sentiments = {
        "aggressive": "🔴",
        "warning": "🟠",
        "defensive": "🟡",
        "diplomatic": "🟢",
        "neutral": "⚪"
    }
    return sentiments.get(sentiment.lower(), "⚪")


def get_latest_statements() -> list:
    """
    Leader statements, cached in MongoDB for LEADERS_CACHE_HOURS (24h).
    Fresh fetch = 5 Tavily searches + 1 LLM extraction.
    """
    cached = get_cached_statements(hours=LEADERS_CACHE_HOURS)
    if cached is not None:
        print("⚡ Leader statements served from cache")
        return cached

    print("🔍 Fetching fresh leader statements...")
    from tools.tavily_search import search_military_news

    queries = [
        "Trump military statement today",
        "Putin Ukraine announcement today",
        "Netanyahu Gaza statement today",
        "Xi Jinping military today",
        "Khamenei Iran statement today",
    ]
    # The 5 searches are independent network calls — run them concurrently
    # (sequential took ~10-15s cold; this is bounded by the slowest single call).
    from concurrent.futures import ThreadPoolExecutor

    def _safe_search(q):
        try:
            return search_military_news(q) or []
        except Exception as e:
            print(f"⚠️ Tavily failed for '{q}': {e}")
            return []

    all_articles = []
    with ThreadPoolExecutor(max_workers=len(queries)) as pool:
        for batch in pool.map(_safe_search, queries):
            all_articles.extend(batch)

    statements = extract_from_articles(all_articles)
    if statements:
        save_statements(statements)
        print(f"💾 Saved {len(statements)} statements")
    return statements


def extract_from_articles(articles: list) -> list:
    """Extract leader quotes from articles"""

    if not articles:
        return []

    content = ""
    for art in articles[:10]:
        title = art.get("title", "")
        text = art.get("content", "")[:300]
        content += f"Title: {title}\nContent: {text}\n\n"

    leader_names = [v["leader"] for v in TRACKED_LEADERS.values()]
    leaders_str = ", ".join(leader_names)

    prompt = f"""You are a military intelligence analyst.
Extract direct quotes or statements from world leaders.

Leaders to find: {leaders_str}

Articles:
{content}

Return ONLY a JSON array:
[
    {{
        "leader": "name",
        "country": "country",
        "flag": "flag emoji",
        "role": "their role",
        "statement": "what they said",
        "context": "brief context",
        "sentiment": "aggressive/diplomatic/defensive/warning/neutral",
        "source": "article title"
    }}
]

Only include leaders who appear in articles!
Return [] if none found.
Return ONLY JSON!"""

    try:
        statements = chat_json(prompt, max_tokens=1500)
        if not isinstance(statements, list):
            raise LLMError("expected a JSON array")
        print(f"✅ Found {len(statements)} statements")
        return statements
    except LLMError as e:
        print(f"❌ Leader extraction failed: {e}")
        return []


def test_leader_tracker():
    """Test leader tracker"""
    
    print("🧪 Testing Leader Tracker...")
    print("="*50)
    
    statements = get_latest_statements()
    
    if statements:
        for s in statements:
            flag = s.get("flag", "🌍")
            leader = s.get("leader", "Unknown")
            role = s.get("role", "")
            statement = s.get("statement", "")
            sentiment = s.get("sentiment", "neutral")
            context = s.get("context", "")
            emoji = get_sentiment_emoji(sentiment)
            
            print(f"\n{flag} {leader} ({role})")
            print(f"{emoji} Sentiment: {sentiment}")
            print(f"💬 \"{statement}\"")
            print(f"📌 Context: {context}")
    else:
        print("⚠️ No statements found!")
        print("💡 Search some news first in SENTINEL AI!")


if __name__ == "__main__":
    test_leader_tracker()