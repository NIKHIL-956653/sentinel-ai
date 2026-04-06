from pydantic import BaseModel
from typing import List, Optional

class ArticleModel(BaseModel):
    title: str
    url: str
    content: Optional[str]
    source: str

class StoryModel(BaseModel):
    confidence: str
    emoji: str
    source_count: int
    sources: List[str]
    titles: List[str]
    verdict: Optional[str]
    trust_score: Optional[int]

class NewsResponse(BaseModel):
    status: str
    query: str
    total_articles: int
    total_stories: int
    contradictions: List[dict]
    results: List[dict]

class NewsRequest(BaseModel):
    query: str