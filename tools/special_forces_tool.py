import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# MongoDB cache
try:
    from database import get_db
    db = get_db()
    forces_collection = db["special_forces"]
    MONGO_AVAILABLE = True
except:
    MONGO_AVAILABLE = False
    forces_cache = {}

def get_special_forces(country: str) -> list:
    """
    Get special forces and intelligence units
    for ANY country using LLM!
    Cached in MongoDB for future use.
    """

    # Check cache first
    if MONGO_AVAILABLE:
        cached = forces_collection.find_one({"country": country})
        if cached:
            print(f"Cache hit for {country} special forces!")
            return cached["forces"]
    else:
        if country in forces_cache:
            return forces_cache[country]

    # Generate with LLM
    print(f"Generating special forces for {country}...")

    prompt = f"""List the special forces, intelligence agencies, 
and elite military units of {country}.

Return ONLY a JSON array of strings.
Each string should be in this format:
"[EMOJI] UNIT NAME — Brief description"

Include 6-8 units maximum.
Use military emojis: ⚔️ 🕵️ 💀 🔱 🛡️ 🪂 🔍 🌐

Example format:
["⚔️ Special Forces Unit — Description",
 "🕵️ Intelligence Agency — Description"]

Return ONLY the JSON array. No other text."""

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
                "max_tokens": 500
            }
        )

        content = response.json()["choices"][0]["message"]["content"]

        # Clean and parse JSON
        content = content.strip()
        if "```" in content:
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]

        forces = json.loads(content)

        # Cache in MongoDB
        if MONGO_AVAILABLE:
            forces_collection.insert_one({
                "country": country,
                "forces": forces
            })
        else:
            forces_cache[country] = forces

        return forces

    except Exception as e:
        print(f"Error generating forces for {country}: {e}")
        return [
            f"⚔️ {country} Armed Forces — National Military",
            f"🕵️ {country} Intelligence Service — State Security",
            f"🛡️ {country} Special Operations — Elite Units"
        ]