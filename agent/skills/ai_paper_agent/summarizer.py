"""Paper summarization — skill-specific module.

Generates concise summaries of papers using the LLM in batches.
Uses shared/llm.py for all LLM calls.
"""

import json
import logging

from agent.shared.llm import call_llm

logger = logging.getLogger(__name__)

SUMMARIZE_BATCH_SIZE = 5

SUMMARIZER_SYSTEM_PROMPT = (
    "You are a research paper summarizer. For each paper, write exactly "
    "3 concise sentences:\n"
    "1. What problem does it address?\n"
    "2. What is the approach/method?\n"
    "3. What are the key results or contributions?\n\n"
    "Be specific and technical. No filler words.\n"
    "Respond ONLY with a valid JSON array, no other text.\n"
    'Format: [{"index": 0, "summary": "..."}]'
)


def summarize_papers(papers: list[dict]) -> list[dict]:
    """Generate 3-sentence summaries for papers in batches.

    Args:
        papers: List of paper dicts with 'title' and 'abstract'.

    Returns:
        Same list with 'summary' field added to each paper.
    """
    for i in range(0, len(papers), SUMMARIZE_BATCH_SIZE):
        batch = papers[i : i + SUMMARIZE_BATCH_SIZE]
        batch_text = ""
        for j, paper in enumerate(batch):
            abstract = (paper.get("abstract") or "No abstract available.")[:600]
            batch_text += f"\n[{j}] Title: {paper['title']}\nAbstract: {abstract}\n"

        prompt = f"Summarize each paper below:\n{batch_text}"

        try:
            results = call_llm(prompt, system=SUMMARIZER_SYSTEM_PROMPT, expect_json=True)
            for entry in results:
                idx = entry.get("index", 0)
                if 0 <= idx < len(batch):
                    batch[idx]["summary"] = entry.get("summary", "")
            summarized = sum(1 for p in batch if p.get("summary"))
            logger.info(f"Summarized batch {i // SUMMARIZE_BATCH_SIZE + 1}: {summarized}/{len(batch)} papers")
        except (json.JSONDecodeError, Exception) as e:
            logger.warning(f"Batch summarization failed ({e}), falling back to individual calls")
            for paper in batch:
                _summarize_single(paper)

    return papers


def _summarize_single(paper: dict):
    """Fallback: summarize a single paper individually."""
    abstract = (paper.get("abstract") or "No abstract available.")[:800]
    prompt = f"Title: {paper['title']}\n\nAbstract: {abstract}\n\nSummarize in 3 sentences:"
    try:
        paper["summary"] = call_llm(prompt, system=SUMMARIZER_SYSTEM_PROMPT.split("\n")[0])
    except Exception as e:
        logger.error(f"Summarization failed for '{paper['title'][:60]}': {e}")
        paper["summary"] = paper.get("abstract", "")[:200] + "..."
