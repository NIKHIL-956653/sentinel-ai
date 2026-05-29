import requests

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

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

def extract_leader_statements(articles: list) -> list:
    """
    Extract leader quotes from news articles
    Uses LLM to find quotes!
    Zero extra Tavily credits! 😄
    """
    
    if not articles:
        return []
    
    # Prepare article content
    content = ""
    for article in articles[:5]:  # Use last 5 articles
        for story in article.get("results", []):
            for art in story.get("articles", []):
                title = art.get("title", "")
                text = art.get("content", "")[:500]
                content += f"Title: {title}\nContent: {text}\n\n"
    
    if not content:
        return []
    
    # Leaders to look for
    leader_names = [v["leader"] for v in TRACKED_LEADERS.values()]
    leaders_str = ", ".join(leader_names)
    
    prompt = f"""You are a military intelligence analyst.
Read these news articles and extract any direct quotes or statements 
from world leaders.

Leaders to look for: {leaders_str}

News Articles:
{content}

Return ONLY a JSON array:
[
    {{
        "leader": "leader name",
        "country": "country name",
        "flag": "country flag emoji",
        "role": "their role",
        "statement": "what they said (direct quote or paraphrase)",
        "context": "brief context of why they said it",
        "sentiment": "aggressive/diplomatic/defensive/warning/neutral",
        "source": "article title"
    }}
]

Only include leaders who actually appear in the articles!
If no leaders found return empty array: []
Return ONLY JSON, no other text."""

    try:
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 1500
            }
        )
        
        if response.status_code == 200:
            import json
            data = response.json()
            content_response = data['choices'][0]['message']['content']
            
            content_response = content_response.strip()
            if "```json" in content_response:
                content_response = content_response.split("```json")[1].split("```")[0]
            elif "```" in content_response:
                content_response = content_response.split("```")[1].split("```")[0]
            
            statements = json.loads(content_response.strip())
            print(f"✅ Found {len(statements)} leader statements!")
            return statements
            
    except Exception as e:
        print(f"❌ Error: {e}")
    
    return []


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
    Get leader statements - cached for 24 hours!
    Only fetches fresh once per day!
    """
    print("🔍 Using NEW function with Tavily!")
    from database import db
    from datetime import datetime, timedelta

    print("👤 Checking leader statements cache...")

    # Check MongoDB cache first!
    cutoff = datetime.utcnow() - timedelta(hours=24)
    cached = db["leader_statements"].find_one({
        "timestamp": {"$gte": cutoff}
    })

    if cached:
        print("⚡ Serving from cache!")
        return cached["statements"]

    print("🔍 Fetching fresh leader statements...")

    from tools.tavily_search import search_military_news

    all_articles = []

    # Search top 5 leaders only!
    top_leaders = [
        "Trump military statement today",
        "Putin Ukraine announcement today",
        "Netanyahu Gaza statement today",
        "Xi Jinping military today",
        "Khamenei Iran statement today"
    ]

    for query in top_leaders:
        print(f"🔍 Searching: {query}")
        articles = search_military_news(query)
        if articles:
            all_articles.extend(articles)

    # Extract statements with LLM
    statements = extract_from_articles(all_articles)

    # Save to MongoDB for 24 hours!
    if statements:
        db["leader_statements"].delete_many({})
        db["leader_statements"].insert_one({
            "timestamp": datetime.utcnow(),
            "statements": statements
        })
        print(f"💾 Saved {len(statements)} statements!")

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
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "openai/gpt-oss-120b",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1500
            }
        )

        if response.status_code == 200:
            import json
            data = response.json()
            content_resp = data['choices'][0]['message']['content']

            content_resp = content_resp.strip()
            if "```json" in content_resp:
                content_resp = content_resp.split("```json")[1].split("```")[0]
            elif "```" in content_resp:
                content_resp = content_resp.split("```")[1].split("```")[0]

            statements = json.loads(content_resp.strip())
            print(f"✅ Found {len(statements)} statements!")
            return statements

    except Exception as e:
        print(f"❌ Error: {e}")

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