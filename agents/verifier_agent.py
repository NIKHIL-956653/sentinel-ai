from datetime import datetime, timezone
from tools.confidence_scorer import verify_news

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
    
    def check_contradictions(self, results: list) -> list:
        """Check for contradicting stories"""
        
        contradictions = []
        
        for i, story1 in enumerate(results):
            for j, story2 in enumerate(results):
                if i >= j:
                    continue
                    
                title1 = story1["titles"][0].lower()
                title2 = story2["titles"][0].lower()
                
                # Check for contradiction keywords
                contradiction_pairs = [
                    ("victory", "defeat"),
                    ("advance", "retreat"),
                    ("ceasefire", "attack"),
                    ("peace", "war"),
                    ("captured", "liberated")
                ]
                
                for word1, word2 in contradiction_pairs:
                    if (word1 in title1 and word2 in title2) or \
                       (word2 in title1 and word1 in title2):
                        contradictions.append({
                            "story1": story1["titles"][0],
                            "story2": story2["titles"][0],
                            "conflict": f"{word1} vs {word2}"
                        })
        
        return contradictions
    
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
            
            # Calculate trust score
            trust_score = (
                len(trust["trusted"]) * 2 +
                len(trust["unknown"]) * 1 +
                len(trust["unreliable"]) * -2
            )
            
            # Final verdict
            if trust_score >= 2 and \
               story["confidence"] in ["HIGH", "MEDIUM"]:
                verdict = "VERIFIED ✅"
            elif len(trust["unreliable"]) > 0:
                verdict = "DISPUTED ❌"
            elif story["confidence"] == "LOW":
                verdict = "UNVERIFIED ⚠️"
            else:
                verdict = "NEEDS REVIEW 🔍"
            
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
                print(f"  ⚡ {c['conflict']}: {c['story1'][:30]} vs {c['story2'][:30]}")
        
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