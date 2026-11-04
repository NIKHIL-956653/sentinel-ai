"""
Entity extraction for the knowledge graph.

One LLM call per fresh search: for every story, the named people, organisations, weapons /
platforms and places it mentions. Stored as story["entities"] = [{"name","type"}] and later
assembled into a graph (services/graph.py) linking stories ↔ entities ↔ countries ↔ leaders.

Fail-soft: errors → entities = [] on every story.
"""
import re

from tools.llm import chat_json, LLMError

ENTITY_TYPES = ("person", "organisation", "weapon", "place")
MAX_PER_STORY = 8

_TYPE_ALIASES = {"org": "organisation", "organization": "organisation", "company": "organisation",
                 "location": "place", "country": "place", "city": "place", "region": "place",
                 "people": "person", "leader": "person", "platform": "weapon", "system": "weapon",
                 "equipment": "weapon", "vehicle": "weapon", "aircraft": "weapon", "ship": "weapon"}


def canonical(name: str) -> str:
    """Key used to merge "U.S. Navy" / "US Navy" style duplicates."""
    return re.sub(r"[^a-z0-9]+", " ", (name or "").replace(".", "").lower()).strip()


def parse_entities(raw, n_stories: int) -> dict:
    out = {}
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            i = int(item.get("story"))
        except (TypeError, ValueError):
            continue
        if not (0 <= i < n_stories):
            continue
        ents = item.get("entities")
        if not isinstance(ents, list):
            continue
        bucket = out.setdefault(i, [])
        seen = {canonical(e["name"]) for e in bucket}
        for e in ents:
            if len(bucket) >= MAX_PER_STORY:
                break
            if not isinstance(e, dict):
                continue
            name = str(e.get("name", "")).strip()[:80]
            t = str(e.get("type", "")).strip().lower()
            t = _TYPE_ALIASES.get(t, t)
            if not name or t not in ENTITY_TYPES or canonical(name) in seen:
                continue
            seen.add(canonical(name))
            bucket.append({"name": name, "type": t})
    return out


def extract_entities(stories: list) -> list:
    """Attach story['entities']. Never raises."""
    for s in stories:
        s.setdefault("entities", [])
    if not stories:
        return stories
    lines = [f"[{i}] {(s.get('titles') or ['?'])[0]}" for i, s in enumerate(stories)]
    prompt = f"""Extract named entities from each headline below. Types: person, organisation, weapon
(a specific weapon system, platform, missile, aircraft, ship class), place (country, city, sea, region).
Use the most common English name (e.g. "United States", "Vladimir Putin", "F-35"). Max {MAX_PER_STORY} per headline.

Headlines:
{chr(10).join(lines)}

Return ONLY a JSON array: [{{"story": <index>, "entities": [{{"name": "...", "type": "person|organisation|weapon|place"}}]}}]"""
    try:
        parsed = parse_entities(chat_json(prompt, max_tokens=1200), len(stories))
        for i, ents in parsed.items():
            stories[i]["entities"] = ents
        print(f"🕸️  entities: {sum(len(v) for v in parsed.values())} across {len(parsed)} stories")
    except LLMError as e:
        print(f"⚠️ entity extraction skipped: {e}")
    return stories
