import requests
import json
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

def get_country_military_profile(country: str) -> dict:
    """
    Fetch country military profile from Wikipedia
    Uses search API - works for ANY country!
    """
    
    print(f"🌍 Fetching military profile: {country}")
    
    try:
        # Step 1: Search Wikipedia
        search_url = "https://en.wikipedia.org/w/api.php"
        
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{country} armed forces military",
            "format": "json",
            "srlimit": 1
        }
        
        response = requests.get(
            search_url,
            params=params,
            headers={"User-Agent": "SENTINEL-AI/1.0"}
        )
        
        summary = ""
        source_url = ""
        
        if response.status_code == 200:
            data = response.json()
            results = data["query"]["search"]
            
            if results:
                page_title = results[0]["title"]
                print(f"✅ Found page: {page_title}")
                
                # Step 2: Fetch summary
                summary_response = requests.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}",
                    headers={"User-Agent": "SENTINEL-AI/1.0"}
                )
                
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    summary = summary_data.get("extract", "")
                    source_url = summary_data.get(
                        "content_urls", {}
                    ).get("desktop", {}).get("page", "")
                    print(f"✅ Got summary! Length: {len(summary)}")
        
        # Step 3: Structure with LLM
        if summary:
            profile = structure_military_data(
                country,
                summary,
                source_url
            )
        else:
            profile = get_basic_profile(country)
            
        return profile
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return get_basic_profile(country)


def structure_military_data(country: str,
                             raw_data: str,
                             source_url: str = "") -> dict:
    """Use LLM to structure military data"""
    
    prompt = f"""You are a military intelligence analyst.
Based on this Wikipedia data about {country}'s military:

{raw_data}

Extract and return ONLY a JSON object:
{{
    "country": "{country}",
    "military_summary": "2-3 sentence overview",
    "army_strength": "number or estimate or N/A",
    "navy_strength": "number or estimate or N/A",
    "airforce_strength": "number or estimate or N/A",
    "defense_budget": "amount in USD or N/A",
    "global_rank": "number or N/A",
    "key_weapons": ["weapon1", "weapon2", "weapon3"],
    "notable_facts": ["fact1", "fact2"],
    "data_source": "Wikipedia",
    "source_url": "{source_url}",
    "data_availability": "official"
}}

If data not available for a field use "Officially Not Available"
Return ONLY the JSON, no other text."""

    print(f"🤖 Calling OpenRouter...")
    print(f"📝 Summary length: {len(raw_data)}")

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
                "max_tokens": 1000
            }
        )
        print(f"📡 OpenRouter status: {response.status_code}")
        print(f"📡 Response: {response.text[:200]}")

        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            print(f"🤖 LLM Raw Response: {content[:300]}")

            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            profile = json.loads(content.strip())
            profile["data_source"] = "Wikipedia"
            profile["source_url"] = source_url
            print(f"✅ Profile structured for {country}!")
            return profile
            
    except Exception as e:
        print(f"❌ LLM error: {e}")
        import traceback
        traceback.print_exc()
    
    return get_basic_profile(country)


def get_basic_profile(country: str) -> dict:
    """When data unavailable"""
    return {
        "country": country,
        "military_summary": "Officially Not Available",
        "army_strength": "Officially Not Available",
        "navy_strength": "Officially Not Available",
        "airforce_strength": "Officially Not Available",
        "defense_budget": "Officially Not Available",
        "global_rank": "Officially Not Available",
        "key_weapons": [],
        "notable_facts": [],
        "data_source": "No official data found",
        "source_url": ""
    }


def test_wikipedia_tool():
    """Test with multiple countries"""
    
    countries = ["India", "UAE", "Belarus"]
    
    for country in countries:
        print(f"\n{'='*50}")
        profile = get_country_military_profile(country)
        print(f"🌍 {profile['country']}")
        print(f"📊 {profile['military_summary']}")
        print(f"🪖 Army: {profile['army_strength']}")
        print(f"⚓ Navy: {profile['navy_strength']}")
        print(f"✈️ Airforce: {profile['airforce_strength']}")
        print(f"💰 Budget: {profile['defense_budget']}")
        print(f"🚀 Weapons: {profile['key_weapons']}")
        print(f"🔗 Source: {profile['source_url']}")


if __name__ == "__main__":
    test_wikipedia_tool()