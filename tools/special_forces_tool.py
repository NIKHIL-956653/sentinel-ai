"""Special forces / intelligence units per country — LLM-generated, Wikipedia-grounded, cached in MongoDB."""
from database import forces_collection, cache_get, cache_put
from tools.llm import chat_json, LLMError
from tools.grounding import ground_items

FALLBACK = [
    {"emoji": "⚔️", "name": "{c} Armed Forces", "description": "National military", "wiki_title": None},
    {"emoji": "🕵️", "name": "{c} Intelligence Service", "description": "State security", "wiki_title": None},
    {"emoji": "🛡️", "name": "{c} Special Operations", "description": "Elite units", "wiki_title": None},
]


def get_special_forces(country: str) -> list:
    key = f"{country.strip().lower()}_v2"   # v2 = object items with grounding
    cached = cache_get(forces_collection, key)
    if cached is not None:
        print(f"⚡ Cache hit: special forces {country}")
        return cached

    print(f"🤖 Generating special forces for {country}...")
    prompt = f"""List the special forces, intelligence agencies and elite military units of {country}.

Return ONLY a JSON array of 6-8 objects:
[{{"emoji": "⚔️", "name": "Unit name", "description": "one sentence",
   "wiki_title": "exact English Wikipedia article title, or null if no article exists"}}]

Use military emojis: ⚔️ 🕵️ 💀 🔱 🛡️ 🪂 🔍 🌐. Only include units you are confident exist."""
    try:
        forces = chat_json(prompt, max_tokens=700)
        if not isinstance(forces, list):
            raise LLMError("expected a JSON array")
        forces = ground_items(forces)
        cache_put(forces_collection, key, forces, country=country)
        return forces
    except LLMError as e:
        print(f"❌ Special forces generation failed for {country}: {e}")
        return [{**f, "name": f["name"].format(c=country), "source_url": None, "grounded": False} for f in FALLBACK]
