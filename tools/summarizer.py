import requests
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

def summarize_article(title: str, content: str, source: str) -> str:
    """
    Summarize article using OpenRouter
    CIA style intelligence brief!
    """
    
    if not content or len(content) < 100:
        return "Insufficient content for analysis."
    
    prompt = f"""You are a military intelligence analyst.
Analyze this news article and provide a brief intelligence report.

Title: {title}
Source: {source}
Content: {content}

Provide a structured intelligence brief with:
1. SITUATION: What is happening? (2-3 sentences)
2. KEY ACTORS: Who is involved?
3. SIGNIFICANCE: Why does this matter militarily?
4. ASSESSMENT: What could happen next?

Keep it concise, factual, and intelligence-focused.
Format it clearly with the headers."""

    try:
        response = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemma-3-4b-it:free",
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 500
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            summary = data['choices'][0]['message']['content']
            print(f"✅ Summary generated for: {title[:30]}...")
            return summary
        else:
            print(f"❌ OpenRouter error: {response.status_code}")
            print(f"❌ Response: {response.text}")  # ADD THIS LINE!
            return "Summary unavailable at this time."
            
    except Exception as e:
        print(f"❌ Summarizer error: {e}")
        return "Summary unavailable at this time."


def test_summarizer():
    """Test the summarizer"""
    
    test_title = "Trump warns Iran over Strait of Hormuz"
    test_content = """
    US President Donald Trump issued a final warning to Iran,
    threatening military action if the Strait of Hormuz is blocked.
    Iran responded by calling the ultimatum helpless and nervous.
    The strait carries 20% of global oil supplies.
    Military vessels from both sides are positioned in the Gulf.
    """
    test_source = "aljazeera.com"
    
    print("🧪 Testing summarizer...")
    summary = summarize_article(
        test_title, 
        test_content,
        test_source
    )
    print(f"\n📊 INTELLIGENCE BRIEF:\n{summary}")


if __name__ == "__main__":
    test_summarizer()