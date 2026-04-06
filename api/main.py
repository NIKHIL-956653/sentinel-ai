from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes.news import router

# Initialize FastAPI app
app = FastAPI(
    title="SENTINEL AI",
    description="Military Intelligence & News Verification Platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Include routes
app.include_router(router, prefix="/api/v1")

@app.get("/")
async def root():
    return {
        "service": "SENTINEL AI 🕵️",
        "status": "ONLINE",
        "version": "1.0.0",
        "endpoints": {
            "news": "/api/v1/news",
            "health": "/api/v1/health",
            "docs": "/docs"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )