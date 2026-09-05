"""
The ONE place SENTINEL talks to the LLM.

Every tool used to carry its own copy of the OpenRouter request + JSON-fence
stripping. That meant 7 hardcoded model names and 7 places to fix a bug.
Now: chat() for text, chat_json() for structured output. Model comes from
config.OPENROUTER_MODEL (env OPENROUTER_MODEL).
"""
import json
import requests

from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL, LLM_TIMEOUT_SECONDS


class LLMError(RuntimeError):
    pass


def chat(prompt: str, max_tokens: int = 1000, model: str | None = None) -> str:
    """Single-turn completion. Raises LLMError on any failure."""
    if not OPENROUTER_API_KEY:
        raise LLMError("OPENROUTER_API_KEY is not set (check .env)")
    try:
        r = requests.post(
            f"{OPENROUTER_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}",
                     "Content-Type": "application/json"},
            json={"model": model or OPENROUTER_MODEL,
                  "messages": [{"role": "user", "content": prompt}],
                  "max_tokens": max_tokens},
            timeout=LLM_TIMEOUT_SECONDS,
        )
    except requests.RequestException as e:
        raise LLMError(f"OpenRouter request failed: {e}") from e
    if r.status_code != 200:
        raise LLMError(f"OpenRouter {r.status_code}: {r.text[:200]}")
    try:
        return r.json()["choices"][0]["message"]["content"]
    except (KeyError, IndexError, ValueError) as e:
        raise LLMError(f"Unexpected OpenRouter response: {r.text[:200]}") from e


def strip_fences(text: str) -> str:
    """Remove ```json ... ``` wrappers models like to add."""
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        # take the first fenced block that looks like JSON
        for part in parts[1:]:
            body = part[4:] if part.startswith("json") else part
            if body.strip().startswith(("{", "[")):
                return body.strip()
    return t


def chat_json(prompt: str, max_tokens: int = 1000, model: str | None = None):
    """Completion parsed as JSON. Raises LLMError if the model did not return JSON."""
    raw = chat(prompt, max_tokens=max_tokens, model=model)
    try:
        return json.loads(strip_fences(raw))
    except json.JSONDecodeError as e:
        raise LLMError(f"Model did not return valid JSON: {raw[:200]}") from e
