"""Shared LLM interface for calling Qwen via Ollama.

Provides a clean, reusable interface for all skills to call the local LLM.
Handles retries, JSON parsing, and timeout management.
"""

import json
import logging
import time

import requests

from agent.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 600  # 10 minutes — generous for slower hardware
MAX_RETRIES = 3
RETRY_BACKOFF = 5  # seconds, doubled each retry


def call_llm(
    prompt: str,
    system: str = "",
    model: str | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    expect_json: bool = False,
    max_retries: int = MAX_RETRIES,
) -> str | dict | list:
    """Call the local LLM via Ollama API with retry on transient failures.

    Args:
        prompt: The user/task prompt.
        system: Optional system prompt.
        model: Model name (defaults to config).
        timeout: Request timeout in seconds.
        expect_json: If True, parse response as JSON and return parsed object.
        max_retries: Number of retry attempts on transient failures.

    Returns:
        Response text (str) or parsed JSON (dict/list) if expect_json=True.

    Raises:
        requests.RequestException: If the API call fails after all retries.
        json.JSONDecodeError: If expect_json=True and response isn't valid JSON.
    """
    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    last_error = None
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json=payload,
                timeout=timeout,
            )
            resp.raise_for_status()
            text = resp.json().get("response", "").strip()

            if expect_json:
                return parse_json_response(text)

            return text
        except (requests.Timeout, requests.ConnectionError) as e:
            last_error = e
            wait = RETRY_BACKOFF * (2 ** attempt)
            logger.warning(f"LLM call attempt {attempt + 1}/{max_retries} failed: {e}. Retrying in {wait}s...")
            time.sleep(wait)
        except requests.RequestException:
            raise

    raise last_error


def parse_json_response(text: str) -> dict | list:
    """Parse JSON from LLM response, handling markdown code blocks."""
    cleaned = text.strip()

    # Handle ```json ... ``` blocks
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0].strip()

    return json.loads(cleaned)


def is_ollama_running() -> bool:
    """Check if Ollama server is running and the model is available."""
    try:
        resp = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        resp.raise_for_status()
        models = [m["name"] for m in resp.json().get("models", [])]
        return any(OLLAMA_MODEL in m for m in models)
    except Exception:
        return False
