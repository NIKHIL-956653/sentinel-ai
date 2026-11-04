"""
Timeline: how a query's stories evolved across runs.

Every /news run is archived in Mongo; this joins those runs by story key (normalised headline,
same key the watchlist uses) and returns, per story, one cell per run with confidence / verdict /
claim status — so the UI can draw a strip: "first seen LOW on Monday, HIGH + VERIFIED by Wednesday,
disputed on Thursday". Pure `build_timeline(runs)` is unit-tested; the route feeds it history.
"""
from services.watchlist import story_key
from database import get_query_history


def build_timeline(runs: list) -> dict:
    runs = [r for r in runs if isinstance(r, dict)]
    columns = []
    rows = {}
    for ri, run in enumerate(runs):
        ts = run.get("timestamp")
        results = run.get("results") or []
        columns.append({
            "run": ri,
            "timestamp": ts.isoformat() + "Z" if hasattr(ts, "isoformat") else ts,
            "total_stories": len(results),
            "high": sum(1 for s in results if (s.get("confidence") or "").upper() == "HIGH"),
            "verified": sum(1 for s in results if (s.get("verdict") or "").startswith("VERIFIED")),
            "contradictions": len(run.get("contradictions") or []),
        })
        for s in results:
            key = story_key(s)
            if not key:
                continue
            row = rows.setdefault(key, {"key": key, "title": (s.get("titles") or [""])[0], "first_run": ri,
                                        "cells": {}, "url": ((s.get("articles") or [{}])[0]).get("url")})
            claims = s.get("claims") or []
            row["cells"][ri] = {
                "confidence": (s.get("confidence") or "").upper(),
                "verdict": s.get("verdict", ""),
                "sources": s.get("source_count") or len(s.get("sources") or []),
                "disputed_claims": sum(1 for c in claims if c.get("status") == "disputed"),
            }
            row["last_run"] = ri
    out_rows = []
    for row in rows.values():
        cells = [row["cells"].get(i) for i in range(len(runs))]
        first, last = row["cells"][row["first_run"]], row["cells"][row["last_run"]]
        rank = {"HIGH": 3, "MEDIUM": 2, "LOW": 1}
        trend = "up" if rank.get(last["confidence"], 0) > rank.get(first["confidence"], 0) else \
                "down" if rank.get(last["confidence"], 0) < rank.get(first["confidence"], 0) else "flat"
        out_rows.append({"key": row["key"], "title": row["title"], "url": row["url"], "first_run": row["first_run"],
                         "last_run": row["last_run"], "runs_seen": len(row["cells"]), "trend": trend, "cells": cells})
    out_rows.sort(key=lambda r: (-r["runs_seen"], r["first_run"]))
    return {"runs": columns, "stories": out_rows}


def timeline_for(query: str, days: int = 7) -> dict:
    runs = get_query_history(query, days=days)
    tl = build_timeline(runs)
    tl.update({"query": query, "days": days})
    return tl
