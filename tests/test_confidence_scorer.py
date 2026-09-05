from tools.confidence_scorer import (calculate_similarity, content_words, group_similar_articles,
                                     score_confidence)


def art(title, source="x.com"):
    return {"title": title, "source": source, "url": f"https://{source}/a", "content": ""}


def test_content_words_drops_stopwords_and_short_tokens():
    assert content_words("The army of Northland is at war") == {"army", "northland", "war"}


def test_similarity_requires_two_shared_words():
    # only "northland" shared → 0
    assert calculate_similarity("Northland budget vote", "Northland missile test") == 0.0
    # two shared → positive
    assert calculate_similarity("Northland forces enter Karim", "Karim falls to Northland forces") > 0.3


def test_grouping_merges_paraphrases_and_separates_topics():
    arts = [
        art("Northland forces enter border town of Karim", "reuters.com"),
        art("Karim falls as Northland troops advance", "bbc.com"),
        art("Southmark parliament approves record defence budget", "aljazeera.com"),
    ]
    groups = group_similar_articles(arts)
    assert len(groups) == 2
    sizes = sorted(len(g["articles"]) for g in groups)
    assert sizes == [1, 2]


def test_confidence_levels_by_distinct_sources():
    hi = {"sources": ["reuters.com", "bbc.com", "aljazeera.com"], "titles": ["t"], "articles": []}
    md = {"sources": ["reuters.com", "bbc.com"], "titles": ["t"], "articles": []}
    lo = {"sources": ["reuters.com", "reuters.com"], "titles": ["t"], "articles": []}  # same outlet twice
    assert score_confidence(hi)["confidence"] == "HIGH"
    assert score_confidence(md)["confidence"] == "MEDIUM"
    assert score_confidence(lo)["confidence"] == "LOW"
