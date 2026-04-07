from fastapi import APIRouter, HTTPException
from api.models.news_model import NewsRequest, NewsResponse
from agents.collector_agent import CollectorAgent
from agents.verifier_agent import VerifierAgent
from database import save_news_results, get_cached_results

router = APIRouter()

collector = CollectorAgent()
verifier = VerifierAgent()

@router.post("/news", response_model=NewsResponse)
async def get_news(request: NewsRequest):
    try:
        print(f"\n🌐 API Request: {request.query}")
        
        # Step 1: Check cache first!
        cached = get_cached_results(
            request.query, 
            hours=1
        )
        
        if cached:
            print("⚡ Serving from cache!")
            return NewsResponse(
                status="cached",
                query=cached["query"],
                total_articles=cached["total_articles"],
                total_stories=cached["total_stories"],
                contradictions=cached["contradictions"],
                results=cached["results"]
            )
        
        # Step 2: Fresh fetch!
        collected = collector.collect(request.query)
        
        if collected["status"] == "failed":
            raise HTTPException(
                status_code=404,
                detail="No articles found!"
            )
        
        # Step 3: Verify
        verified = verifier.verify(collected)
        
        # Step 4: Save to MongoDB!
        save_data = {
            "total_articles": collected["total_articles"],
            "total_stories": verified["total_stories"],
            "results": verified["results"],
            "contradictions": verified["contradictions"]
        }
        save_news_results(request.query, save_data)
        
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
    return {
        "status": "online",
        "service": "SENTINEL AI",
        "version": "2.0.0",
        "database": "MongoDB connected ✅"
    }

@router.get("/recent")
async def get_recent():
    from database import get_recent_news
    recent = get_recent_news(hours=24)
    return {
        "status": "success",
        "total": len(recent),
        "searches": recent
    }