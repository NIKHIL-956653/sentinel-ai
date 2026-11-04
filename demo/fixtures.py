"""
DEMO_MODE fixtures: canned, clearly fictional data so the whole product can be explored with no API
keys and no network. Place names (Northland, Southmark, Eastria, Westoria, Karim, Port Velen) are the
same fictional ones as eval/dataset.json — nothing here describes a real event.

Used by: tools/tavily_search (articles), tools/llm (every LLM prompt), tools/wikipedia_tool (profile).
The LLM stand-in recognises prompts by distinctive phrases from each real prompt template; if a
template changes, update the marker here (tests/test_demo.py checks every pipeline stage still works).
"""
import json
import random

DEMO_BANNER = "DEMO MODE — fictional data, no API keys, no network. Nothing shown here describes a real event."

_SOURCES = ["reuters.com", "bbc.com", "aljazeera.com", "apnews.com", "theguardian.com", "rt.com", "defensewire.example"]

_STORIES = [
    # (headlines that cluster into ONE story, country for geotag, entities)
    # 0 ─ corroborated by 1 (different wording, so the clusterer keeps them apart; the claim extractor links them)
    (["Northland forces enter border town of Karim", "Karim falls as Northland troops advance",
      "Northland army takes Karim after two-day assault"], "Ukraine",
     [("Northland Army", "organisation"), ("Karim", "place"), ("General Varo", "person"), ("T-90", "weapon")]),
    (["Residents flee westward as fighting reaches the Karim outskirts"], "Ukraine",
     [("Karim", "place"), ("Red Crescent", "organisation")]),
    # 2 ─ contradicted by 3
    (["Northland shelling continues despite announced ceasefire"], "Ukraine",
     [("Northland Army", "organisation"), ("Ceasefire Monitoring Mission", "organisation")]),
    (["Monitors report a calm front line for a third consecutive day"], "Ukraine",
     [("Ceasefire Monitoring Mission", "organisation")]),
    # 4+ ─ filler that varies per query
    (["Southmark parliament approves record defence budget",
      "Southmark lawmakers back largest military spending bill in decades"], "Poland",
     [("Southmark Parliament", "organisation"), ("Prime Minister Elin Kasta", "person")]),
    (["Eastria test-fires long-range missile over the northern sea"], "North Korea",
     [("Eastria Strategic Forces", "organisation"), ("Hwasal-9", "weapon"), ("Northern Sea", "place")]),
    (["Westoria pledges air-defence systems to Southmark",
      "Westoria to send air-defence batteries to Southmark within weeks"], "Germany",
     [("Westoria", "place"), ("IRIS-T", "weapon"), ("Chancellor Mara Holt", "person")]),
    (["Port Velen refinery fire under control, officials say"], "Iran",
     [("Port Velen", "place"), ("Velen Petroleum", "organisation")]),
    (["Tanker seized by Northland patrol boats in the strait, crew detained"], "Strait of Hormuz",
     [("Northland Navy", "organisation"), ("MV Coral Dawn", "weapon")]),
]
# story-index relations the fake LLM asserts (resolved to prompt indices at call time)
_SUPPORTS = {0: [1]}          # story 0's main claim is supported by story 1
_CONTRADICTS = {2: [3], 3: [2]}
_CLAIMS = {
    0: ["Northland forces entered Karim", "The assault on Karim lasted two days"],
    1: ["Civilians are leaving the Karim area"],
    2: ["Shelling continues on the Northland front"],
    3: ["The Northland front line has been calm for three days"],
}
_CITY = {0: "Kharkiv", 1: "Kharkiv"}


def demo_articles(query: str) -> list:
    """7-11 articles whose mix depends on the query, so different searches look different."""
    rnd = random.Random(query.strip().lower())
    out = []
    for i, (titles, _, _) in enumerate(_STORIES):
        if i >= 4 and rnd.random() < 0.35:      # the first four stories always appear (they carry the demo's story)
            continue
        for j, t in enumerate(titles):
            src = _SOURCES[(i * 3 + j) % len(_SOURCES)]
            n = (i * 7 + j * 3) % 20
            out.append({
                "title": t,
                "url": f"https://{src}/demo/{i}-{j}",
                "content": f"{t}. Officials said {n} people were affected; details are still emerging. "
                           f"(Fictional demo article — query: {query})",
                "source": src,
                "score": round(0.6 + rnd.random() * 0.4, 2),
            })
    rnd.shuffle(out)
    return out


def _story_index(prompt: str) -> list:
    """Headlines in the order the prompt lists them ([i] prefix), so answers reference the right indices."""
    import re
    return re.findall(r"^\[(\d+)\] (.+?)(?: — |$)", prompt, flags=re.M)


def _match(title: str):
    """Which fixture story a (possibly «»-wrapped, truncated) headline belongs to."""
    clean = title.strip().strip("«»")
    for si, (titles, country, ents) in enumerate(_STORIES):
        if any(t[:28] in clean for t in titles):
            return si, country, ents
    return None, None, []


def demo_llm(prompt: str) -> str:
    p = prompt
    if "incompatible factual claims about the same event" in p:          # contradiction judge
        rows = _story_index(p)
        by_si = {}
        for i, t in rows:
            si = _match(t)[0]
            if si is not None:
                by_si.setdefault(si, int(i))
        pairs, seen = [], set()
        for si, others in _CONTRADICTS.items():
            for o in others:
                if si in by_si and o in by_si and (o, si) not in seen:
                    seen.add((si, o))
                    pairs.append({"a": by_si[si], "b": by_si[o], "conflict": "one says shelling continues, the other says the front is calm"})
        return json.dumps(pairs)
    if "atomic, checkable factual claims" in p:                          # claims
        rows = _story_index(p)
        by_si = {}
        for i, t in rows:
            si = _match(t)[0]
            if si is not None:
                by_si.setdefault(si, int(i))
        out = []
        for i, t in rows:
            si = _match(t)[0]
            texts = _CLAIMS.get(si) or [t.strip("«»").split(",")[0]]
            claims = []
            for k, text in enumerate(texts):
                sup = [by_si[o] for o in _SUPPORTS.get(si, []) if o in by_si and by_si[o] != int(i)] if k == 0 else []
                con = [by_si[o] for o in _CONTRADICTS.get(si, []) if o in by_si and by_si[o] != int(i)] if k == 0 else []
                claims.append({"text": text, "supported_by": sup, "contradicted_by": con})
            out.append({"story": int(i), "claims": claims})
        return json.dumps(out)
    if "Extract named entities" in p:                                    # entities
        out = []
        for i, t in _story_index(p):
            _, _, ents = _match(t)
            out.append({"story": int(i), "entities": [{"name": n, "type": ty} for n, ty in ents]})
        return json.dumps(out)
    if "name the ONE country or region" in p:                            # geotag
        out = []
        for i, t in _story_index(p):
            si, country, _ = _match(t)
            if country:
                item = {"i": int(i), "country": country}
                if si in _CITY:
                    item["place"] = _CITY[si]
                out.append(item)
        return json.dumps(out)
    if "situation report (SITREP)" in p:                                  # brief
        return json.dumps({
            "headline": "Karim falls as ceasefire reports conflict; Southmark re-arms",
            "assessment": "Fictional demo assessment: Northland's capture of Karim is corroborated by three outlets [0], "
                          "while reporting on the ceasefire is split [3]. Southmark's budget vote and Westorian air-defence pledge signal a longer confrontation [1][4].",
            "top_developments": ["Northland forces take Karim after a two-day assault [0]",
                                 "Southmark approves a record defence budget [1]",
                                 "Westoria pledges air-defence batteries to Southmark [4]",
                                 "Eastria long-range missile test over the northern sea [2]"],
            "contradictions": ["Ceasefire: monitors say it holds, frontline reports say shelling continues [3]"],
            "leader_statements": ["Prime Minister Elin Kasta: budget is 'deterrence, not escalation' (fictional)"],
            "watch_items": ["Counter-attack on Karim", "Delivery timeline of Westorian air-defence batteries"],
        })
    if "Based on this Wikipedia data" in p:                               # country profile
        return json.dumps(demo_profile("Demo"))
    if "Compare these two militaries" in p:
        return ("Fictional demo analysis: both forces are sized for regional deterrence; the first has the larger "
                "land component, the second the more modern air fleet. Overall conventional advantage: the larger budget.")
    if "world leader's statement" in p:
        return "Fictional demo analysis: the statement signals resolve to a domestic audience and warns neighbours; expect diplomatic follow-up rather than immediate action."
    if "leader" in p.lower() and "statement" in p.lower():               # leader tracker extraction
        return json.dumps([{"leader": "Prime Minister Elin Kasta", "role": "Prime Minister", "country": "Southmark",
                            "statement": "This budget is deterrence, not escalation.", "sentiment": "diplomatic",
                            "context": "Fictional: said after the parliamentary vote.", "source": "demo"},
                           {"leader": "General Varo", "role": "Chief of Staff", "country": "Northland",
                            "statement": "Karim is only the first step.", "sentiment": "aggressive",
                            "context": "Fictional: televised address.", "source": "demo"}])
    if "wiki_title" in p:                                                 # weapons / special forces lists
        return json.dumps([{"name": "Demo Item Alpha", "year": "2001", "type": "fictional", "history": "Fictional demo entry.", "wiki_title": None},
                           {"name": "Demo Item Bravo", "year": "2015", "type": "fictional", "history": "Fictional demo entry.", "wiki_title": None}])
    return json.dumps([])


def demo_profile(country: str) -> dict:
    return {
        "country": country,
        "military_summary": f"DEMO: fictional summary for {country}. Branch figures below are placeholders, "
                            f"budget / personnel / rank (if shown) come from the real World Bank open dataset.",
        "army_strength": "~250,000 (demo)", "navy_strength": "~40,000 (demo)", "airforce_strength": "~60,000 (demo)",
        "defense_budget": "N/A", "global_rank": "N/A",
        "key_weapons": ["Demo Item Alpha", "Demo Item Bravo"],
        "notable_facts": ["This dossier is generated by DEMO_MODE — nothing here is real."],
        "data_source": "DEMO fixtures + World Bank open data (SIPRI/IISS) where available",
        "source_url": "", "data_availability": "demo",
        "estimates_note": "DEMO MODE: branch figures are placeholders.",
    }
