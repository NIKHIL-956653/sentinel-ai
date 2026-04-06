from difflib import SequenceMatcher

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts"""
    return SequenceMatcher(None, 
                          text1.lower(), 
                          text2.lower()).ratio()

def group_similar_articles(articles: list, 
                          threshold: float = 0.3) -> list:
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
            
            if similarity > threshold:
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