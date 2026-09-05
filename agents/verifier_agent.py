from config import CONTRADICTION_MODE
from tools.llm import chat_json, LLMError

# Keyword pairs used by the heuristic detector (cheap, offline, but blunt: "peace" vs "war"
# fires on unrelated stories). The LLM judge is the default; this is the fallback.
CONTRADICTION_PAIRS = [
    ("victory", "defeat"),
    ("advance", "retreat"),
    ("ceasefire", "attack"),
    ("peace", "war"),
    ("captured", "liberated"),
    ("denies", "confirms"),
    ("killed", "survived"),
]

# Trusted sources list
TRUSTED_SOURCES = [
    "reuters.com",
    "bbc.com",
    "apnews.com",
    "defense.gov",
    "nato.int",
    "wikipedia.org",
    "aljazeera.com",
    "theguardian.com"
]

# Unreliable sources list
UNRELIABLE_SOURCES = [
    "rt.com",           # Russian state media
    "presstv.com",      # Iranian state media
    "globalresearch.ca" # Known misinformation
]

class VerifierAgent:
    """
    SENTINEL AI - Verifier Agent
    Checks quality, trustworthiness and contradictions
    """
    
    def __init__(self):
        self.name = "Verifier Agent"
        self.role = "Intelligence Verifier"
        print(f"🔎 {self.name} initialized!")
    
    def check_source_trust(self, sources: list) -> dict:
        """Check if sources are trusted"""
        
        trusted = []
        unreliable = []
        unknown = []
        
        for source in sources:
            if any(t in source for t in TRUSTED_SOURCES):
                trusted.append(source)
            elif any(u in source for u in UNRELIABLE_SOURCES):
                unreliable.append(source)
            else:
                unknown.append(source)
        
        return {
            "trusted": trusted,
            "unreliable": unreliable,
            "unknown": unknown
        }
    
    @staticmethod
    def trust_score(trust: dict) -> int:
        """+2 per trusted source, +1 per unknown, -2 per unreliable."""
        return len(trust["trusted"]) * 2 + len(trust["unknown"]) * 1 + len(trust["unreliable"]) * -2

    @classmethod
    def verdict_for(cls, trust: dict, confidence: str) -> str:
        """
        Pure decision rule — kept separate so it can be unit-tested and evaluated.
        VERIFIED requires at least one *trusted* source: two unknown blogs agreeing is
        "NEEDS REVIEW", not verified (this was a gap in the original rule).
        """
        score = cls.trust_score(trust)
        if trust["trusted"] and score >= 2 and confidence in ("HIGH", "MEDIUM"):
            return "VERIFIED ✅"
        if trust["unreliable"]:
            return "DISPUTED ❌"
        if confidence == "LOW":
            return "UNVERIFIED ⚠️"
        return "NEEDS REVIEW 🔍"

    # ── Contradictions ─────────────────────────────────────────────────────
    @staticmethod
    def check_contradictions_keyword(results: list) -> list:
        """Heuristic: opposing keyword pairs across two story headlines."""
        contradictions = []
        for i, story1 in enumerate(results):
            for j, story2 in enumerate(results):
                if i >= j:
                    continue
                t1 = story1["titles"][0].lower()
                t2 = story2["titles"][0].lower()
                for w1, w2 in CONTRADICTION_PAIRS:
                    if (w1 in t1 and w2 in t2) or (w2 in t1 and w1 in t2):
                        contradictions.append({
                            "story1": story1["titles"][0],
                            "story2": story2["titles"][0],
                            "conflict": f"{w1} vs {w2}",
                            "method": "keyword",
                        })
                        break
        return contradictions

    @staticmethod
    def check_contradictions_llm(results: list) -> list:
        """
        One LLM call per search: the model reads every story (headline + snippet) and returns the
        pairs that make incompatible factual claims. Raises LLMError so the caller can fall back.
        """
        if len(results) < 2:
            return []
        lines = []
        for idx, story in enumerate(results):
            title = story["titles"][0]
            snippet = ""
            arts = story.get("articles") or []
            if arts and arts[0].get("content"):
                snippet = arts[0]["content"][:240].replace("\n", " ")
            lines.append(f"[{idx}] {title}" + (f" — {snippet}" if snippet else ""))
        prompt = f"""You are a fact-checking analyst. Below are news stories about the same topic,
each with an index in square brackets.

Two stories CONTRADICT when they make incompatible factual claims about the same event
(e.g. one says a ceasefire holds, the other says strikes continued today; one says 12 killed,
the other says no casualties). Different angles, different sub-events, or one being more
detailed are NOT contradictions.

Stories:
{chr(10).join(lines)}

Return ONLY a JSON array (empty array if none). Each item:
{{"a": <index>, "b": <index>, "conflict": "<one short sentence saying what is incompatible>"}}"""
        raw = chat_json(prompt, max_tokens=600)
        if not isinstance(raw, list):
            raise LLMError("contradiction judge did not return a list")
        out, seen = [], set()
        for item in raw:
            try:
                a, b = int(item["a"]), int(item["b"])
            except (KeyError, TypeError, ValueError):
                continue
            if a == b or not (0 <= a < len(results)) or not (0 <= b < len(results)):
                continue
            key = (min(a, b), max(a, b))
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "story1": results[key[0]]["titles"][0],
                "story2": results[key[1]]["titles"][0],
                "conflict": str(item.get("conflict", "")).strip()[:300] or "incompatible claims",
                "method": "llm",
            })
        return out

    def check_contradictions(self, results: list) -> list:
        """LLM judge by default (CONTRADICTION_MODE=llm), keyword heuristic as fallback / opt-in."""
        if CONTRADICTION_MODE == "llm":
            try:
                return self.check_contradictions_llm(results)
            except LLMError as e:
                print(f"⚠️ LLM contradiction check failed ({e}); using keyword heuristic")
        return self.check_contradictions_keyword(results)

    def verify(self, collected_data: dict) -> dict:
        """
        Main verification function
        Input: collected data from CollectorAgent
        Output: verified + quality checked data
        """
        
        print(f"\n{'='*50}")
        print(f"🔎 VERIFIER AGENT ON DUTY!")
        print(f"{'='*50}")
        
        results = collected_data.get("results", [])
        verified_results = []
        
        for story in results:
            # Check source trust
            trust = self.check_source_trust(
                story["sources"]
            )
            
            trust_score = self.trust_score(trust)
            verdict = self.verdict_for(trust, story["confidence"])
            
            story["trust"] = trust
            story["trust_score"] = trust_score
            story["verdict"] = verdict
            verified_results.append(story)
            
            print(f"\n📰 {story['titles'][0][:50]}...")
            print(f"🏆 Verdict: {verdict}")
            print(f"✅ Trusted sources: {trust['trusted']}")
            print(f"🚩 Unreliable sources: {trust['unreliable']}")
        
        # Check contradictions
        contradictions = self.check_contradictions(results)
        
        if contradictions:
            print(f"\n⚡ CONTRADICTIONS FOUND: {len(contradictions)}")
            for c in contradictions:
                print(f"  ⚡ [{c.get('method')}] {c['conflict'][:60]}: {c['story1'][:30]} vs {c['story2'][:30]}")
        
        print(f"\n{'='*50}")
        print(f"🔎 VERIFICATION COMPLETE!")
        print(f"{'='*50}")
        
        return {
            "status": "verified",
            "query": collected_data["query"],
            "total_stories": len(verified_results),
            "contradictions": contradictions,
            "results": verified_results
        }


def test_verifier():
    """Test verifier with collector"""
    from agents.collector_agent import CollectorAgent
    
    # Collect first
    collector = CollectorAgent()
    collected = collector.collect(
        "Russia Ukraine war latest 2026"
    )
    
    # Then verify
    verifier = VerifierAgent()
    verified = verifier.verify(collected)
    
    print(f"\n📊 Final Stories: {verified['total_stories']}")
    print(f"⚡ Contradictions: {len(verified['contradictions'])}")


if __name__ == "__main__":
    test_verifier()