"""Paper scoring — reusable domain tool.

Two-stage scoring:
1. Pre-filter using open-source signals (HF upvotes, etc.) — fast, free
2. LLM scoring on papers that pass pre-filter — slower, deeper analysis

Uses shared/llm.py for all LLM calls.
"""

import json
import logging

from agent.config import SCORE_BATCH_SIZE, TOPICS
from agent.shared.llm import call_llm

logger = logging.getLogger(__name__)


def prefilter_by_signals(papers: list[dict]) -> list[dict]:
    """Pre-filter papers using open-source quality signals.

    Currently arXiv is the only source, so all papers pass through.
    This function is kept for extensibility when additional sources
    with quality signals (e.g. upvotes) are added in the future.
    """
    logger.info(f"Pre-filter: {len(papers)} papers (all pass — arXiv only source)")
    return papers


def score_papers(papers: list[dict], topics: list[str] | None = None) -> list[dict]:
    """Score papers in batches using the LLM. Adds 'score' and 'category' fields.

    Should be called AFTER prefilter_by_signals() to reduce LLM calls.

    Args:
        papers: List of paper dicts with 'title' and 'abstract'.
        topics: Interest areas for scoring context. Defaults to config TOPICS.

    Returns:
        Same list with 'score' (int 0-10) and 'category' (str) added to each paper.
    """
    # TOPICS is list of (query, weight) tuples; extract just the query strings
    raw = topics or TOPICS
    topic_queries = [t[0] if isinstance(t, tuple) else t for t in raw]
    topics_str = "\n".join(f"- {q}" for q in topic_queries)
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
            signals = p.get("quality_signals", {})
            signal_str = ""
            if signals:
                signal_str = f" | Signals: {signals}"
            batch_text += f"\n[{j}] Title: {p['title']}\nAbstract: {abstract}{signal_str}\n"

        prompt = (
            f"Rate each paper below for relevance (0-10) and assign a category "
            f"(one of: llm, agents, multimodal, infra).\n"
            f"Respond ONLY with valid JSON array, no other text.\n"
            f'Format: [{{"index": 0, "score": 8, "category": "agents"}}]\n'
            f"\nPapers:{batch_text}"
        )

        try:
            scores = call_llm(prompt, system=system_prompt, expect_json=True)
            for entry in scores:
                idx = entry.get("index", 0)
                if 0 <= idx < len(batch):
                    batch[idx]["score"] = entry.get("score", 0)
                    batch[idx]["category"] = entry.get("category", "llm")
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Scoring batch {i // SCORE_BATCH_SIZE} failed: {e}")
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
