import os
from dotenv import load_dotenv

load_dotenv()

# App Settings
APP_NAME = "SENTINEL AI"
APP_VERSION = "1.0.0"
DEV_MODE = True

# API Keys
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# OpenRouter Settings
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "openai/gpt-oss-120b"

# Tavily Settings
TAVILY_MAX_RESULTS = 3 if DEV_MODE else 10
TAVILY_SEARCH_DEPTH = "advanced"
TAVILY_INCLUDE_DOMAINS = [
    "reuters.com",
    "bbc.com",
    "aljazeera.com",
    "defense.gov",
    "nato.int",
    "wikipedia.org"
]

# RAG Settings
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Vector Store
VECTOR_STORE_PATH = "vector_store"

# Confidence Scoring
HIGH_CONFIDENCE_THRESHOLD = 3
LOW_CONFIDENCE_THRESHOLD = 1