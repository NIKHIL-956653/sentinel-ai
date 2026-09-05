"""
Test bootstrap: make the repo importable and guarantee tests never touch a real
MongoDB or spend API credits. Set BEFORE any project module is imported.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

os.environ["MONGODB_URI"] = "mongodb://127.0.0.1:1"      # nothing listens here → fail-soft paths
os.environ["OPENROUTER_API_KEY"] = "test-key-never-used"  # llm.chat is always mocked
os.environ["TAVILY_API_KEY"] = "test"
os.environ["SENTINEL_API_KEY"] = ""                      # security tests reload with their own value
os.environ["CONTRADICTION_MODE"] = "llm"

# .env in the repo would override the values above via load_dotenv → neutralise it for tests
import dotenv  # noqa: E402
dotenv.load_dotenv = lambda *a, **k: False
