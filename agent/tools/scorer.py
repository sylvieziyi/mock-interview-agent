"""Qwen-based paper scoring via Ollama."""

import json
import logging

import requests

from agent.config import OLLAMA_BASE_URL, OLLAMA_MODEL, SCORE_BATCH_SIZE, TOPICS

logger = logging.getLogger(__name__)


def _call_ollama(prompt: str, system: str = "") -> str:
    """Call Ollama's generate API and return the response text."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
    }
    if system:
        payload["system"] = system

    resp = requests.post(
        f"{OLLAMA_BASE_URL}/api/generate",
        json=payload,
        timeout=300,  # generous timeout for CPU inference
    )
    resp.raise_for_status()
    return resp.json().get("response", "")


def score_papers(papers: list[dict]) -> list[dict]:
    """Score papers in batches using Qwen. Adds 'score' and 'category' fields."""
    topics_str = "\n".join(f"- {t}" for t in TOPICS)
    system_prompt = (
        "You are a research paper evaluator. You rate papers on relevance to the "
        "user's interests. Be strict — only highly relevant, high-quality papers "
        "should score 7 or above.\n\n"
        f"User's interest areas:\n{topics_str}"
    )

    scored = []
    for i in range(0, len(papers), SCORE_BATCH_SIZE):
        batch = papers[i : i + SCORE_BATCH_SIZE]
        batch_text = ""
        for j, p in enumerate(batch):
            abstract = (p.get("abstract") or "No abstract available.")[:500]
            batch_text += f"\n[{j}] Title: {p['title']}\nAbstract: {abstract}\n"

        prompt = (
            f"Rate each paper below for relevance (0-10) and assign a category "
            f"(one of: llm, agents, multimodal, infra).\n"
            f"Respond ONLY with valid JSON array, no other text.\n"
            f"Format: [{{\"index\": 0, \"score\": 8, \"category\": \"agents\"}}]\n"
            f"\nPapers:{batch_text}"
        )

        try:
            response = _call_ollama(prompt, system=system_prompt)
            # Try to parse JSON from the response
            # Handle cases where model wraps JSON in markdown code blocks
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("\n", 1)[-1].rsplit("```", 1)[0]
            scores = json.loads(cleaned)

            for entry in scores:
                idx = entry.get("index", 0)
                if 0 <= idx < len(batch):
                    batch[idx]["score"] = entry.get("score", 0)
                    batch[idx]["category"] = entry.get("category", "llm")
        except (json.JSONDecodeError, requests.RequestException) as e:
            logger.error(f"Scoring batch {i // SCORE_BATCH_SIZE} failed: {e}")
            # Assign default scores so the pipeline continues
            for p in batch:
                p.setdefault("score", 0)
                p.setdefault("category", "llm")

        scored.extend(batch)

    scored_count = sum(1 for p in scored if p.get("score", 0) > 0)
    logger.info(f"Scored {scored_count}/{len(scored)} papers successfully")
    return scored


def filter_by_threshold(papers: list[dict], min_score: int = 7) -> list[dict]:
    """Keep only papers with score >= min_score."""
    filtered = [p for p in papers if p.get("score", 0) >= min_score]
    logger.info(f"Filtered: {len(filtered)}/{len(papers)} papers passed threshold {min_score}")
    return filtered
