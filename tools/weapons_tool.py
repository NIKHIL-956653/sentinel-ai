import requests
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL

def get_weapon_details(weapon_name: str, country: str = "") -> dict:
    """
    Fetch weapon specifications from Wikipedia
    Returns detailed weapon specs!
    """
    
    print(f"🔍 Fetching weapon details: {weapon_name}")
    
    try:
        # Search Wikipedia for weapon
        search_url = "https://en.wikipedia.org/w/api.php"
        
        params = {
            "action": "query",
            "list": "search",
            "srsearch": f"{weapon_name} weapon military specifications",
            "format": "json",
            "srlimit": 1
        }
        
        response = requests.get(
            search_url,
            params=params,
            headers={"User-Agent": "SENTINEL-AI/1.0"}
        )
        
        summary = ""

        if response.status_code == 200:
            data = response.json()
            results = data["query"]["search"]
            
            if results:
                page_title = results[0]["title"]
                print(f"✅ Found: {page_title}")
                
                # Fetch summary
                summary_response = requests.get(
                    f"https://en.wikipedia.org/api/rest_v1/page/summary/{page_title.replace(' ', '_')}",
                    headers={"User-Agent": "SENTINEL-AI/1.0"}
                )
                
                if summary_response.status_code == 200:
                    summary_data = summary_response.json()
                    summary = summary_data.get("extract", "")

                    # Get full content for better specs!
                    full_response = requests.get(
                        f"https://en.wikipedia.org/w/api.php?action=query&titles={page_title.replace(' ', '_')}&prop=extracts&exintro=false&format=json",
                        headers={"User-Agent": "SENTINEL-AI/1.0"}
                    )
                    if full_response.status_code == 200:
                        full_data = full_response.json()
                        pages = full_data["query"]["pages"]
                        for page_id in pages:
                            full_text = pages[page_id].get("extract", "")
                            if full_text:
                                summary = full_text[:3000]  # First 3000 chars
                                break

                    # thumbnail removed - showing wrong images
                    thumbnail = ""
        
        if summary:
            specs = extract_weapon_specs(
                weapon_name,
                country,
                summary
            )
            if thumbnail:
                specs["image"] = thumbnail
            return specs
        else:
            return get_basic_weapon(weapon_name, country)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return get_basic_weapon(weapon_name, country)


def extract_weapon_specs(
    weapon_name: str,
    country: str,
    raw_data: str
) -> dict:
    """Use LLM to extract weapon specifications"""
    
    prompt = f"""You are a military weapons expert.
Provide detailed specifications for: {weapon_name}

Additional context from Wikipedia:
{raw_data[:1000]}

Return ONLY a JSON object:
{{
    "name": "{weapon_name}",
    "country_of_origin": "country name",
    "type": "missile/tank/fighter jet/etc",
    "description": "2-3 sentence overview",
    "specifications": {{
        "speed": "exact value with units",
        "range": "exact value with units",
        "weight": "exact value with units",
        "length": "exact value with units",
        "crew": "number",
        "payload": "exact value with units"
    }},
    "first_used": "year",
    "status": "active/retired/in development",
    "fun_fact": "interesting fact"
}}

Use your knowledge to fill specifications.
Return ONLY JSON."""

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
                "max_tokens": 800
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            content = data['choices'][0]['message']['content']
            
            import json
            content = content.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            specs = json.loads(content.strip())
            print(f"✅ Specs extracted for {weapon_name}!")
            return specs
            
    except Exception as e:
        print(f"❌ LLM error: {e}")
    
    return get_basic_weapon(weapon_name, country)


def get_basic_weapon(weapon_name: str, 
                      country: str = "") -> dict:
    """Basic weapon info when data unavailable"""
    return {
        "name": weapon_name,
        "country_of_origin": country,
        "type": "Military Weapon",
        "description": "Detailed specs not available",
        "specifications": {
            "speed": "Officially Not Available",
            "range": "Officially Not Available",
            "weight": "Officially Not Available",
            "length": "Officially Not Available",
            "crew": "Officially Not Available",
            "payload": "Officially Not Available"
        },
        "first_used": "Officially Not Available",
        "status": "Unknown",
        "fun_fact": "Data not available",
        "source_url": ""
    }


def test_weapons():
    """Test weapon details"""
    
    weapons = [
        ("BrahMos", "India"),
        ("F-16 Fighting Falcon", "USA"),
        ("T-72 Tank", "Russia")
    ]
    
    for weapon, country in weapons:
        print(f"\n{'='*50}")
        specs = get_weapon_details(weapon, country)
        print(f"\n🚀 {specs['name']}")
        print(f"🌍 Country: {specs['country_of_origin']}")
        print(f"📋 Type: {specs['type']}")
        print(f"📝 {specs['description']}")
        print(f"\n⚙️ SPECIFICATIONS:")
        for key, val in specs['specifications'].items():
            print(f"  {key}: {val}")
        print(f"📅 First Used: {specs['first_used']}")
        print(f"✅ Status: {specs['status']}")
        print(f"💡 Fun Fact: {specs['fun_fact']}")


if __name__ == "__main__":
    test_weapons()