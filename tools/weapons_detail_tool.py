import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

try:
    from database import get_db
    db = get_db()
    weapons_cache = db["weapons_detail_cache"]
    MONGO_AVAILABLE = True
except:
    MONGO_AVAILABLE = False
    local_cache = {}

def get_weapon_category_details(country: str, category: str) -> list:
    """
    Get detailed info for any weapon category
    for any country using LLM + MongoDB cache!
    
    Categories: submarines, missiles, fighter_jets, 
                warships, tanks, special_forces
    """
    cache_key = f"{country}_{category}"

    # Check MongoDB cache
    if MONGO_AVAILABLE:
        cached = weapons_cache.find_one({"key": cache_key})
        if cached:
            print(f"Cache hit: {cache_key}")
            return cached["data"]
    else:
        if cache_key in local_cache:
            return local_cache[cache_key]

    # Category specific prompts
    prompts = {
        "submarines": f"""List the active submarines of {country}.
For each submarine provide:
- Name and class
- Year commissioned
- Role (attack/ballistic/patrol)
- Areas patrolled
- One interesting historical fact

Return as JSON array:
[{{"name": "...", "class": "...", "year": "...", 
   "role": "...", "patrol_areas": "...", 
   "history": "..."}}]
Max 8 submarines. Return ONLY JSON.""",

        "missiles": f"""List the officially declared missiles of {country}.
For each missile provide:
- Name
- Type (ballistic/cruise/anti-aircraft etc)
- Range
- Year deployed
- Interesting history or origin story

Return as JSON array:
[{{"name": "...", "type": "...", "range": "...",
   "year": "...", "history": "..."}}]
Max 8 missiles. Return ONLY JSON.""",

        "fighter_jets": f"""List the active fighter jets of {country}.
For each jet provide:
- Name and variant
- Year entered service
- Role
- Interesting fact or history

Return as JSON array:
[{{"name": "...", "variant": "...", "year": "...",
   "role": "...", "history": "..."}}]
Max 8 jets. Return ONLY JSON.""",

        "warships": f"""List the major warships of {country}.
For each warship provide:
- Name
- Class/Type
- Year commissioned
- Areas it patrols
- Notable operations or history

Return as JSON array:
[{{"name": "...", "class": "...", "year": "...",
   "patrol_areas": "...", "history": "..."}}]
Max 8 warships. Return ONLY JSON.""",

        "tanks": f"""List the main battle tanks of {country}.
For each tank provide:
- Name/Model
- Year entered service
- Key features
- Combat history

Return as JSON array:
[{{"name": "...", "year": "...", 
   "features": "...", "history": "..."}}]
Max 8 tanks. Return ONLY JSON.""",
    }

    prompt = prompts.get(category, f"""
List key {category} of {country} military.
Return as JSON array with name, year, description fields.
Max 8 items. Return ONLY JSON.""")

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-2.0-flash-lite-001",
                "messages": [
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 1000
            }
        )

        content = response.json()["choices"][0]["message"]["content"]

        # Clean JSON
        content = content.strip()
        if "```" in content:
            parts = content.split("```")
            for part in parts:
                if "[" in part:
                    content = part
                    if content.startswith("json"):
                        content = content[4:]
                    break

        data = json.loads(content.strip())

        # Cache result
        if MONGO_AVAILABLE:
            weapons_cache.insert_one({
                "key": cache_key,
                "country": country,
                "category": category,
                "data": data
            })
        else:
            local_cache[cache_key] = data

        return data

    except Exception as e:
        print(f"Error: {e}")
        return [{"name": "Data unavailable",
                 "history": "Could not fetch details"}]