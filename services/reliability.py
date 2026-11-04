"""
Outlet reliability learned from the archive.

The verifier's trusted / unreliable lists are hand-written. This module computes, per source domain,
how its reporting actually behaved across archived searches — so the lists can be challenged with
evidence instead of opinion:

  appearances        articles from this domain
  stories            distinct stories it appeared in
  corroboration_rate share of its stories that had ≥2 distinct sources (someone else reported it too)
  verified_rate      share of its stories that ended VERIFIED
  disputed_rate      share of its stories that were DISPUTED or part of a flagged contradiction
  solo_rate          share of its stories where it was the only source
  reliability        0..1 composite = 0.5·corroboration + 0.3·verified + 0.2·(1 − disputed)

Honest caveats (also shown in the UI): VERIFIED depends on the trusted list itself (a trusted outlet
is partly scored by its own label), small samples are noisy (sample_note), and "corroborated" means
"other outlets in Tavily's trusted-domain pool said the same" — not ground truth.
Pure `score_sources(stories, contradictions)` is unit-tested; the route feeds it the archive.
"""
from collections import defaultdict

from agents.verifier_agent import TRUSTED_SOURCES, UNRELIABLE_SOURCES

MIN_STORIES_FOR_SCORE = 3


def _list_for(domain: str) -> str:
    if any(t in domain for t in TRUSTED_SOURCES):
        return "trusted"
    if any(u in domain for u in UNRELIABLE_SOURCES):
        return "unreliable"
    return "unknown"


def score_sources(stories: list, contradictions: list | None = None) -> list:
    contradicted_titles = set()
    for c in contradictions or []:
        contradicted_titles.add((c.get("story1") or "").strip().lower())
        contradicted_titles.add((c.get("story2") or "").strip().lower())

    stats = defaultdict(lambda: {"appearances": 0, "stories": 0, "corroborated": 0, "verified": 0, "disputed": 0, "solo": 0})
    for s in stories:
        srcs = s.get("sources") or []
        distinct = set(srcs)
        if not distinct:
            continue
        title = ((s.get("titles") or [""])[0]).strip().lower()
        verdict = s.get("verdict") or ""
        disputed = verdict.startswith("DISPUTED") or title in contradicted_titles \
            or any(c.get("status") == "disputed" for c in (s.get("claims") or []))
        for d in distinct:
            st = stats[d]
            st["appearances"] += srcs.count(d) if isinstance(srcs, list) else 1
            st["stories"] += 1
            st["corroborated"] += 1 if len(distinct) >= 2 else 0
            st["verified"] += 1 if verdict.startswith("VERIFIED") else 0
            st["disputed"] += 1 if disputed else 0
            st["solo"] += 1 if len(distinct) == 1 else 0

    out = []
    for d, st in stats.items():
        n = st["stories"]
        corr, ver, dis, solo = st["corroborated"] / n, st["verified"] / n, st["disputed"] / n, st["solo"] / n
        score = 0.5 * corr + 0.3 * ver + 0.2 * (1 - dis)
        out.append({
            "domain": d, "list": _list_for(d), "appearances": st["appearances"], "stories": n,
            "corroboration_rate": round(corr, 3), "verified_rate": round(ver, 3), "disputed_rate": round(dis, 3),
            "solo_rate": round(solo, 3), "reliability": round(score, 3),
            "sample_note": "small sample" if n < MIN_STORIES_FOR_SCORE else "",
        })
    out.sort(key=lambda r: (-r["stories"], -r["reliability"]))
    return out


def reliability_report(hours: int = 24 * 30) -> dict:
    from database import get_all_stories, get_recent_news
    stories = get_all_stories(hours)
    contradictions = [c for run in get_recent_news(hours) for c in (run.get("contradictions") or [])]
    rows = score_sources(stories, contradictions)
    return {"hours": hours, "stories": len(stories), "sources": rows,
            "method": "corroboration 50% · verified 30% · not-disputed 20%; see services/reliability.py",
            "caveats": ["VERIFIED partly depends on the hand-written trusted list, so trusted outlets get a head start",
                        f"rows with fewer than {MIN_STORIES_FOR_SCORE} stories are flagged 'small sample'",
                        "corroboration = other outlets in the trusted-domain search pool reported the same story, not ground truth"]}
