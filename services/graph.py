"""
Knowledge graph assembled from cached searches (no LLM call — entities were extracted when
the search ran). Nodes: stories, entities (person / organisation / weapon / place), countries
(from geotag). Edges: story→entity (mentions), story→country (located), leader→country (tracked).

Pure function over the stories list so it is unit-testable; the route feeds it `get_all_stories()`.
"""
from tools.entities import canonical
from tools.geotag import normalise as normalise_country

MAX_STORIES = 60


def build_graph(stories: list, query: str | None = None, max_stories: int = MAX_STORIES) -> dict:
    if query:
        q = query.strip().lower()
        stories = [s for s in stories if (s.get("query") or "").strip().lower() == q]
    stories = [s for s in stories if s.get("titles")][:max_stories]

    nodes, edges = {}, []
    ent_degree = {}

    def add_node(nid, **attrs):
        if nid not in nodes:
            nodes[nid] = {"id": nid, **attrs}
        return nodes[nid]

    for idx, s in enumerate(stories):
        sid = f"story:{idx}"
        art = (s.get("articles") or [{}])[0]
        add_node(sid, type="story", label=s["titles"][0][:90], confidence=(s.get("confidence") or "").upper(),
                 verdict=s.get("verdict", ""), url=art.get("url"), query=s.get("query"))
        geo = s.get("geo")
        if geo and geo.get("country"):
            cid = f"place:{canonical(geo['country'])}"
            add_node(cid, type="place", label=geo["country"], country=True)
            edges.append({"from": sid, "to": cid, "rel": "located"})
            ent_degree[cid] = ent_degree.get(cid, 0) + 1
        for e in s.get("entities") or []:
            key = canonical(e.get("name", ""))
            if not key:
                continue
            etype = e.get("type", "organisation")
            # merge "place" entities that are known countries with geotag country nodes
            if etype == "place" and normalise_country(e["name"]):
                key = canonical(normalise_country(e["name"]))
                label = normalise_country(e["name"])
            else:
                label = e["name"]
            eid = f"{etype}:{key}"
            n = add_node(eid, type=etype, label=label)
            if etype == "place" and normalise_country(label):
                n["country"] = True
            if not any(x["from"] == sid and x["to"] == eid for x in edges):
                edges.append({"from": sid, "to": eid, "rel": "mentions"})
                ent_degree[eid] = ent_degree.get(eid, 0) + 1

    # tracked leaders → their country (static knowledge, lets the graph link leader quotes to dossiers)
    try:
        from tools.leader_tracker import TRACKED_LEADERS
        for country, info in TRACKED_LEADERS.items():
            pid = f"person:{canonical(info['leader'])}"
            cid = f"place:{canonical(normalise_country(country) or country)}"
            if pid in nodes and cid in nodes:
                edges.append({"from": pid, "to": cid, "rel": "leads"})
    except Exception:
        pass

    for nid, n in nodes.items():
        n["degree"] = ent_degree.get(nid, 0) if n["type"] != "story" else 1
    return {"nodes": list(nodes.values()), "edges": edges,
            "stats": {"stories": len(stories), "entities": sum(1 for n in nodes.values() if n["type"] != "story"),
                      "edges": len(edges)}}
