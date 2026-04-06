from fastapi import APIRouter, HTTPException
from api.models.news_model import NewsRequest, NewsResponse
from agents.collector_agent import CollectorAgent
from agents.verifier_agent import VerifierAgent

router = APIRouter()

collector = CollectorAgent()
verifier = VerifierAgent()

@router.post("/news", response_model=NewsResponse)
async def get_news(request: NewsRequest):
    """
    Fetch and verify military news
    """
    try:
        print(f"\n🌐 API Request: {request.query}")
        
        # Step 1: Collect
        collected = collector.collect(request.query)
        
        if collected["status"] == "failed":
            raise HTTPException(
                status_code=404,
                detail="No articles found!"
            )
        
        # Step 2: Verify
        verified = verifier.verify(collected)
        
        return NewsResponse(
            status=verified["status"],
            query=verified["query"],
            total_articles=collected["total_articles"],
            total_stories=verified["total_stories"],
            contradictions=verified["contradictions"],
            results=verified["results"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

@router.get("/health")
async def health_check():
    """Check if API is running"""
    return {
        "status": "online",
        "service": "SENTINEL AI",
        "version": "1.0.0"
    }