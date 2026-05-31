from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tools.wikipedia_tool import get_country_military_profile

router = APIRouter()

_cache = {}

known_ranks = {
    "United States": 1, "Russia": 2, "China": 3,
    "India": 4, "United Kingdom": 5, "South Korea": 6,
    "Pakistan": 7, "Japan": 8, "France": 9, "Italy": 10,
    "Turkey": 11, "Israel": 17, "Iran": 14, "UAE": 38,
    "Saudi Arabia": 22, "Germany": 19, "North Korea": 36,
}

@router.get("/country/{country_name}")
async def get_country(country_name: str):
    try:
        if country_name in _cache:
            return _cache[country_name]
        profile = get_country_military_profile(country_name)
        profile["global_rank"] = known_ranks.get(
            country_name,
            profile.get("global_rank", "N/A")
        )
        _cache[country_name] = profile
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weapons/{country_name}/{category}")
async def get_weapons(country_name: str, category: str):
    try:
        from tools.weapons_detail_tool import get_weapon_category_details
        data = get_weapon_category_details(country_name, category)
        return {"country": country_name, "category": category, "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/special-forces/{country_name}")
async def get_special_forces(country_name: str):
    try:
        from tools.special_forces_tool import get_special_forces
        forces = get_special_forces(country_name)
        return {"country": country_name, "forces": forces}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/leaders")
async def get_leaders():
    try:
        from tools.leader_tracker import get_latest_statements
        statements = get_latest_statements()
        return {"statements": statements}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CompareRequest(BaseModel):
    country1: dict
    country2: dict

@router.post("/compare-analysis")
async def compare_analysis(request: CompareRequest):
    try:
        import requests as req
        import os
        a = request.country1
        b = request.country2

        prompt = f"""Compare these two militaries and give a brief analysis:

Country 1: {a.get('country')}
Army: {a.get('army_strength')} | Navy: {a.get('navy_strength')} | Airforce: {a.get('airforce_strength')} | Budget: {a.get('defense_budget')} | Rank: #{a.get('global_rank')}

Country 2: {b.get('country')}
Army: {b.get('army_strength')} | Navy: {b.get('navy_strength')} | Airforce: {b.get('airforce_strength')} | Budget: {b.get('defense_budget')} | Rank: #{b.get('global_rank')}

Give a 3-4 sentence balanced military comparison.
Mention strengths of each. Be factual and neutral.
End with which has overall stronger conventional military power."""

        response = req.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-2.0-flash-lite-001",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        analysis = response.json()["choices"][0]["message"]["content"]
        return {"analysis": analysis}
    except Exception as e:
        return {"analysis": f"Analysis unavailable: {str(e)}"}


class LeaderRequest(BaseModel):
    leader: str
    role: str = ""
    statement: str = ""
    context: str = ""
    sentiment: str = ""

@router.post("/leader-analysis")
async def leader_analysis(request: LeaderRequest):
    try:
        import requests as req
        import os

        prompt = f"""Analyze this world leader's statement from an OSINT perspective.

Leader: {request.leader} ({request.role})
Statement: "{request.statement}"
Context: {request.context}
Sentiment detected: {request.sentiment}

Provide a 3-4 sentence neutral analysis:
1. What this statement signals geopolitically
2. Who it's directed at
3. What action it might precede
4. Overall assessment

Be factual, neutral, and analytical. No bias."""

        response = req.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {os.getenv('OPENROUTER_API_KEY')}",
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-2.0-flash-lite-001",
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        analysis = response.json()["choices"][0]["message"]["content"]
        return {"analysis": analysis}
    except Exception as e:
        return {"analysis": f"Analysis unavailable: {str(e)}"}
