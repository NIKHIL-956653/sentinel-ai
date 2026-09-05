"""Weapon category details per country — LLM-generated, cached in MongoDB."""
from database import weapons_collection, cache_get, cache_put
from tools.llm import chat_json, LLMError
from tools.grounding import ground_items


def get_weapon_category_details(country: str, category: str) -> list:
    """
    Categories: submarines, missiles, fighter_jets, warships, tanks
    """
    cache_key = f"{country.strip().lower()}_{category}_v2"  # v2 = grounded items
    cached = cache_get(weapons_collection, cache_key)
    if cached is not None:
        print(f"⚡ Cache hit: {cache_key}")
        return cached

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
Max 8 submarines. wiki_title must be the exact title of the English Wikipedia article about that item (or null if none). Return ONLY JSON.""",

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
Max 8 missiles. wiki_title must be the exact title of the English Wikipedia article about that item (or null if none). Return ONLY JSON.""",

        "fighter_jets": f"""List the active fighter jets of {country}.
For each jet provide:
- Name and variant
- Year entered service
- Role
- Interesting fact or history

Return as JSON array:
[{{"name": "...", "variant": "...", "year": "...",
   "role": "...", "history": "..."}}]
Max 8 jets. wiki_title must be the exact title of the English Wikipedia article about that item (or null if none). Return ONLY JSON.""",

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
Max 8 warships. wiki_title must be the exact title of the English Wikipedia article about that item (or null if none). Return ONLY JSON.""",

        "tanks": f"""List the main battle tanks of {country}.
For each tank provide:
- Name/Model
- Year entered service
- Key features
- Combat history

Return as JSON array:
[{{"name": "...", "year": "...", 
   "features": "...", "history": "..."}}]
Max 8 tanks. wiki_title must be the exact title of the English Wikipedia article about that item (or null if none). Return ONLY JSON.""",
    }

    prompt = prompts.get(category, f"""
List key {category} of {country} military.
Return as JSON array with name, year, description, wiki_title fields.
Max 8 items. wiki_title must be the exact title of the English Wikipedia article about that item (or null if none). Return ONLY JSON.""")

    try:
        data = chat_json(prompt, max_tokens=1200)
        if not isinstance(data, list):
            raise LLMError("expected a JSON array")
        data = ground_items(data)   # verify wiki_title → source_url / grounded flag
        cache_put(weapons_collection, cache_key, data, country=country, category=category)
        return data
    except LLMError as e:
        print(f"❌ Weapons generation failed ({cache_key}): {e}")
        return [{"name": "Data unavailable",
                 "history": "Could not fetch details"}]