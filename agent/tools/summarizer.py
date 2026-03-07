"""Qwen-based paper summarization via Ollama."""

import logging

import requests

from agent.config import OLLAMA_BASE_URL, OLLAMA_MODEL

logger = logging.getLogger(__name__)


def summarize_paper(papers: list[dict]) -> list[dict]:
    """Generate a 3-sentence summary for each paper using Qwen."""
    system_prompt = (
        "You are a research paper summarizer. Given a paper's title and abstract, "
        "write exactly 3 concise sentences:\n"
        "1. What problem does it address?\n"
        "2. What is the approach/method?\n"
        "3. What are the key results or contributions?\n"
        "Be specific and technical. No filler words."
    )

    for paper in papers:
        abstract = (paper.get("abstract") or "No abstract available.")[:800]
        prompt = f"Title: {paper['title']}\n\nAbstract: {abstract}\n\nSummarize:"

        try:
            resp = requests.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": OLLAMA_MODEL,
                    "prompt": prompt,
                    "system": system_prompt,
                    "stream": False,
                },
                timeout=300,
            )
            resp.raise_for_status()
            paper["summary"] = resp.json().get("response", "").strip()
            logger.info(f"Summarized: {paper['title'][:60]}...")
        except Exception as e:
            logger.error(f"Summarization failed for '{paper['title'][:60]}': {e}")
            paper["summary"] = paper.get("abstract", "")[:200] + "..."

    return papers
