"""Shared LLM interface for calling Qwen via Ollama.

Provides a clean, reusable interface for all skills to call the local LLM.
Handles retries, JSON parsing, and timeout management.
"""

import json
import logging

import requests

from agent.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


def call_llm(
    prompt: str,
    system: str = "",
    model: str | None = None,
    timeout: int = 300,
    expect_json: bool = False,
) -> str | dict | list:
    """Call the local LLM via Ollama API.

    Args:
        prompt: The user/task prompt.
        system: Optional system prompt.
        model: Model name (defaults to config).
        timeout: Request timeout in seconds.
        expect_json: If True, parse response as JSON and return parsed object.

    Returns:
        Response text (str) or parsed JSON (dict/list) if expect_json=True.

    Raises:
        requests.RequestException: If the API call fails.
        json.JSONDecodeError: If expect_json=True and response isn't valid JSON.
    """
    payload = {
        "model": model or OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

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
