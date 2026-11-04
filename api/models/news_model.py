from pydantic import BaseModel, Field
from typing import List, Optional

from config import MAX_QUERY_LENGTH

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
    claim_summary: Optional[dict] = None

class NewsRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=MAX_QUERY_LENGTH, description="Search query (plain text)")


# ── Response models for the 2.2 endpoints (documented in /docs, validated on the way out) ──
class TimelineRun(BaseModel):
    run: int
    timestamp: Optional[str] = None
    total_stories: int
    high: int
    verified: int
    contradictions: int


class TimelineStory(BaseModel):
    key: str
    title: str
    url: Optional[str] = None
    first_run: int
    last_run: int
    runs_seen: int
    trend: str
    cells: List[Optional[dict]]


class TimelineResponse(BaseModel):
    query: str
    days: int
    runs: List[TimelineRun]
    stories: List[TimelineStory]


class GraphNode(BaseModel):
    id: str
    type: str
    label: str
    degree: int = 0
    confidence: Optional[str] = None
    verdict: Optional[str] = None
    url: Optional[str] = None
    query: Optional[str] = None
    country: Optional[bool] = None


class GraphEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    rel: str

    model_config = {"populate_by_name": True}


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
    stats: dict


class BriefSections(BaseModel):
    headline: str
    assessment: str = ""
    top_developments: List[str] = []
    contradictions: List[str] = []
    leader_statements: List[str] = []
    watch_items: List[str] = []
    llm: bool = False


class BriefResponse(BaseModel):
    generated_at: str
    window_hours: int
    model: Optional[str] = None
    counts: dict
    regions: List[list]
    queries: List[str]
    disputed_claims: List[dict]
    sections: BriefSections
    stories: List[dict]
    cached: bool = False


class StatsResponse(BaseModel):
    uptime_s: int
    model: str
    llm: dict
    pipeline: dict
    routes: dict
    budget: Optional[dict] = None


class SourceReliability(BaseModel):
    domain: str
    list: str                      # trusted | unreliable | unknown
    appearances: int
    stories: int
    corroboration_rate: float      # share of its stories that had ≥2 distinct sources
    verified_rate: float
    disputed_rate: float
    solo_rate: float               # share of its stories where it was the only source
    reliability: float             # 0..1 composite (documented in services/reliability.py)
    sample_note: str