"""
Story grouping + confidence scoring.

Similarity = Jaccard overlap of content words (stopwords removed) with a minimum of two shared
words. Replaced difflib.SequenceMatcher on raw titles, which over-merged anything sharing a
country name: on eval/dataset.json clustering F1 went 0.47 → 0.83 (see eval/run_eval.py).
"""
import re
from difflib import SequenceMatcher

STOPWORDS = set("""
a an the of in on at to for from by with and or as after amid over into onto via
says say said its their his her new two three is are was were be been has have had
""".split())

SIMILARITY_THRESHOLD = 0.15   # tuned on the synthetic eval set; see eval/results.json
MIN_SHARED_WORDS = 2


def content_words(text: str) -> set:
    return {w for w in re.findall(r"[a-z0-9]+", (text or "").lower())
            if w not in STOPWORDS and len(w) > 2}


def calculate_similarity(text1: str, text2: str) -> float:
    """Jaccard similarity of content words; 0 unless at least MIN_SHARED_WORDS overlap."""
    a, b = content_words(text1), content_words(text2)
    shared = a & b
    if len(shared) < MIN_SHARED_WORDS:
        return 0.0
    return len(shared) / len(a | b)


def sequence_similarity(text1: str, text2: str) -> float:
    """Legacy character-level similarity (kept for comparison in the eval)."""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()


def group_similar_articles(articles: list,
                          threshold: float = SIMILARITY_THRESHOLD) -> list:
    """Group articles covering the same story"""
    
    groups = []
    used = set()
    
    for i, article in enumerate(articles):
        if i in used:
            continue
            
        group = {
            "articles": [article],
            "sources": [article["source"]],
            "titles": [article["title"]]
        }
        
        for j, other in enumerate(articles):
            if i == j or j in used:
                continue
                
            similarity = calculate_similarity(
                article["title"], 
                other["title"]
            )
            
            if similarity >= threshold:
                group["articles"].append(other)
                group["sources"].append(other["source"])
                group["titles"].append(other["title"])
                used.add(j)
        
        used.add(i)
        groups.append(group)
    
    return groups

def score_confidence(group: dict) -> dict:
    """Score confidence based on source count"""
    
    source_count = len(set(group["sources"]))
    
    if source_count >= 3:
        confidence = "HIGH"
        emoji = "✅"
    elif source_count == 2:
        confidence = "MEDIUM"
        emoji = "⚠️"
    else:
        confidence = "LOW"
        emoji = "🔴"
    
    return {
        "confidence": confidence,
        "emoji": emoji,
        "source_count": source_count,
        "sources": list(set(group["sources"])),
        "titles": group["titles"],
        "articles": group["articles"]
    }

def verify_news(articles: list) -> list:
    """Main verification function"""
    
    print(f"\n🔍 Verifying {len(articles)} articles...")
    
    groups = group_similar_articles(articles)
    results = []
    
    for group in groups:
        scored = score_confidence(group)
        results.append(scored)
        
        print(f"\n{scored['emoji']} {scored['confidence']} CONFIDENCE")
        print(f"📰 {scored['titles'][0]}")
        print(f"🌐 Sources: {', '.join(scored['sources'])}")
        print(f"📊 Source count: {scored['source_count']}")
    
    return results