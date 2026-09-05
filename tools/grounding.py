"""
Grounding for LLM-generated lists (weapons, special forces).

The model is asked to name the Wikipedia article each item comes from. We then verify those
titles exist with ONE batched call to the Wikipedia API and attach the canonical URL. Items
whose article does not exist are kept but flagged `grounded: False` so the UI can label them
"AI-generated · unverified" instead of presenting them as fact.
"""
import requests

WIKI_API = "https://en.wikipedia.org/w/api.php"
HEADERS = {"User-Agent": "SENTINEL-AI/2.0 (OSINT research tool)"}
BATCH = 50  # Wikipedia API limit per request


def verify_wikipedia_titles(titles: list, timeout: int = 8) -> dict:
    """
    {requested_title: canonical_url | None}. Follows redirects/normalisation.
    Network failure → every title maps to None (caller shows 'unverified', never crashes).
    """
    clean = [t.strip() for t in titles if isinstance(t, str) and t.strip()]
    result = {t: None for t in clean}
    if not clean:
        return result
    for i in range(0, len(clean), BATCH):
        chunk = clean[i:i + BATCH]
        try:
            r = requests.get(WIKI_API, headers=HEADERS, timeout=timeout, params={
                "action": "query", "format": "json", "redirects": 1,
                "prop": "info", "inprop": "url", "titles": "|".join(chunk),
            })
            if r.status_code != 200:
                continue
            q = r.json().get("query", {})
            # map requested → normalised → redirected → page
            alias = {}
            for n in q.get("normalized", []):
                alias[n["from"]] = n["to"]
            for rd in q.get("redirects", []):
                alias[rd["from"]] = rd["to"]
            pages = {p["title"]: p for p in q.get("pages", {}).values()}
            for t in chunk:
                final = t
                seen = set()
                while final in alias and final not in seen:
                    seen.add(final)
                    final = alias[final]
                page = pages.get(final)
                if page and "missing" not in page and "invalid" not in page:
                    result[t] = page.get("fullurl") or f"https://en.wikipedia.org/wiki/{final.replace(' ', '_')}"
        except (requests.RequestException, ValueError):
            continue
    return result


def ground_items(items: list, title_key: str = "wiki_title") -> list:
    """Attach source_url / grounded to each dict item using its `wiki_title`."""
    titles = [it.get(title_key) for it in items if isinstance(it, dict) and it.get(title_key)]
    urls = verify_wikipedia_titles(titles) if titles else {}
    out = []
    for it in items:
        if not isinstance(it, dict):
            continue
        url = urls.get((it.get(title_key) or "").strip())
        it = dict(it)
        it["source_url"] = url
        it["grounded"] = bool(url)
        out.append(it)
    return out


def grounding_summary(items: list) -> dict:
    n = len(items)
    g = sum(1 for it in items if it.get("grounded"))
    return {"total": n, "grounded": g, "unverified": n - g}
