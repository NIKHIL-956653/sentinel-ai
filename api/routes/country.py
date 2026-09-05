from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from tools.wikipedia_tool import get_country_military_profile
from tools.llm import chat, LLMError
from database import get_cached_country, save_country_profile

router = APIRouter()

# In-process fallback so repeated requests are still fast when Mongo is down.
_mem_cache = {}


@router.get("/country/{country_name}")
async def get_country(country_name: str):
    try:
        if country_name in _mem_cache:
            return _mem_cache[country_name]
        cached = get_cached_country(country_name)
        if cached:
            _mem_cache[country_name] = cached
            return cached
        profile = get_country_military_profile(country_name)
        # global_rank comes from the open dataset (rank by expenditure) when available;
        # otherwise whatever the Wikipedia/LLM step produced, else N/A
        profile.setdefault("global_rank", "N/A")
        _mem_cache[country_name] = profile
        save_country_profile(country_name, profile)
        return profile
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weapons/{country_name}/{category}")
async def get_weapons(country_name: str, category: str):
    try:
        from tools.weapons_detail_tool import get_weapon_category_details
        from tools.grounding import grounding_summary
        data = get_weapon_category_details(country_name, category)
        return {"country": country_name, "category": category, "data": data,
                "grounding": grounding_summary(data),
                "note": "Items are LLM-generated; those with a source_url were verified to have a matching Wikipedia article."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/special-forces/{country_name}")
async def get_special_forces(country_name: str):
    try:
        from tools.special_forces_tool import get_special_forces
        from tools.grounding import grounding_summary
        forces = get_special_forces(country_name)
        return {"country": country_name, "forces": forces, "grounding": grounding_summary(forces)}
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

        return {"analysis": chat(prompt, max_tokens=400)}
    except LLMError as e:
        return {"analysis": f"Analysis unavailable: {e}"}


class LeaderRequest(BaseModel):
    leader: str
    role: str = ""
    statement: str = ""
    context: str = ""
    sentiment: str = ""

@router.post("/leader-analysis")
async def leader_analysis(request: LeaderRequest):
    try:
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

        return {"analysis": chat(prompt, max_tokens=400)}
    except LLMError as e:
        return {"analysis": f"Analysis unavailable: {e}"}
