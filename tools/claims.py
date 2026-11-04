"""
Claim-level verification.

Headline similarity tells us several outlets cover *a story*; it does not tell us which
*facts* they agree on. One LLM call per fresh search: the model extracts 1-3 atomic factual
claims per story and, for each claim, says which OTHER stories support or contradict it.

Output on every story:
    story["claims"] = [{"text": "...", "supported_by": [idx..], "contradicted_by": [idx..],
                        "status": "corroborated" | "single-source" | "disputed"}]

Fail-soft: any LLM error → `claims` = [] on every story. The parser is pure and unit-tested.
"""
from tools.llm import chat_json, LLMError, untrusted, UNTRUSTED_NOTE

MAX_CLAIMS_PER_STORY = 3


def _snippet(story: dict, n: int = 300) -> str:
    arts = story.get("articles") or []
    if arts and arts[0].get("content"):
        return untrusted(arts[0]["content"], n)
    return ""


def _ints(value, n: int, exclude: int) -> list:
    out = []
    if not isinstance(value, list):
        return out
    for v in value:
        try:
            i = int(v)
        except (TypeError, ValueError):
            continue
        if 0 <= i < n and i != exclude and i not in out:
            out.append(i)
    return out


def claim_status(supported: list, contradicted: list) -> str:
    if contradicted:
        return "disputed"
    return "corroborated" if supported else "single-source"


def parse_claims(raw, n_stories: int) -> dict:
    """{story_index: [claim, ...]} from the model's list; ignores malformed items."""
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
        claims = item.get("claims")
        if not isinstance(claims, list):
            continue
        bucket = out.setdefault(i, [])
        for c in claims:
            if len(bucket) >= MAX_CLAIMS_PER_STORY:
                break
            if not isinstance(c, dict):
                continue
            text = str(c.get("text", "")).strip()[:240]
            if not text:
                continue
            sup = _ints(c.get("supported_by"), n_stories, i)
            con = _ints(c.get("contradicted_by"), n_stories, i)
            bucket.append({"text": text, "supported_by": sup, "contradicted_by": con,
                           "status": claim_status(sup, con)})
    return out


def claim_summary(stories: list) -> dict:
    total = sum(len(s.get("claims") or []) for s in stories)
    corroborated = sum(1 for s in stories for c in (s.get("claims") or []) if c["status"] == "corroborated")
    disputed = sum(1 for s in stories for c in (s.get("claims") or []) if c["status"] == "disputed")
    return {"total": total, "corroborated": corroborated, "disputed": disputed,
            "single_source": total - corroborated - disputed}


def extract_claims(stories: list) -> list:
    """Attach story['claims']. Never raises."""
    for s in stories:
        s.setdefault("claims", [])
    if len(stories) < 1:
        return stories
    lines = []
    for i, s in enumerate(stories):
        title = (s.get("titles") or ["?"])[0]
        snip = _snippet(s)
        lines.append(f"[{i}] {untrusted(title, 200)}" + (f" — {snip}" if snip else ""))
    prompt = f"""You are a fact-checking analyst. Below are news stories about one topic, each with an index.
{UNTRUSTED_NOTE}

For EACH story extract 1 to {MAX_CLAIMS_PER_STORY} atomic, checkable factual claims (who did what, numbers,
dates, places). Then, for each claim, list the indices of OTHER stories whose text supports the same
fact (supported_by) and the indices of stories whose text asserts an incompatible fact (contradicted_by).
Only cite a story if its headline or snippet actually states it. Leave the lists empty when unsure.

Stories:
{chr(10).join(lines)}

Return ONLY a JSON array:
[{{"story": <index>, "claims": [{{"text": "<claim>", "supported_by": [<idx>], "contradicted_by": [<idx>]}}]}}]"""
    try:
        parsed = parse_claims(chat_json(prompt, max_tokens=1400), len(stories))
        for i, claims in parsed.items():
            stories[i]["claims"] = claims
        summ = claim_summary(stories)
        print(f"🧾 claims: {summ['total']} extracted, {summ['corroborated']} corroborated, {summ['disputed']} disputed")
    except LLMError as e:
        print(f"⚠️ claim extraction skipped: {e}")
    return stories
