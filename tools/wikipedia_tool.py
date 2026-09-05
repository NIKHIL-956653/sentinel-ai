import requests
from tools.llm import chat_json, LLMError

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

        # Merge openly licensed statistics (World Bank / SIPRI / IISS) — see tools/military_data.py
        from tools.military_data import get_stats, provenance
        stats = get_stats(country)
        if stats:
            profile.update({k: v for k, v in stats.items() if k not in ("iso3", "wb_name")})
            profile["data_source"] = "Wikipedia (summary) + World Bank open data (SIPRI/IISS)"
            profile["data_provenance"] = provenance()
        else:
            profile["data_source"] = "Wikipedia (summary) — open statistics unavailable"
            profile["data_provenance"] = provenance()
        # Branch strengths come from the LLM's reading of the Wikipedia summary → label them as such
        profile["estimates_note"] = "Army / Navy / Air Force figures are estimates extracted from the Wikipedia summary; budget, personnel and rank are World Bank data with year."

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

    try:
        profile = chat_json(prompt, max_tokens=1000)
        if not isinstance(profile, dict):
            raise LLMError("expected a JSON object")
        profile["data_source"] = "Wikipedia"
        profile["source_url"] = source_url
        print(f"✅ Profile structured for {country}")
        return profile
    except LLMError as e:
        print(f"❌ LLM error: {e}")
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