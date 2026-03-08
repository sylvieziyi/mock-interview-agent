"""Paper scoring — multi-category weighted scoring.

Each paper is scored across multiple dimensions (relevance, novelty, impact,
technical quality). The final score is a weighted average. This produces
more varied and meaningful scores from small models like Qwen 7B compared
to asking for a single holistic score.

Uses shared/llm.py for all LLM calls.
"""

import json
import logging

from agent.config import PAPER_CATEGORIES, SCORE_BATCH_SIZE, SCORING_CATEGORIES, TOPICS
from agent.shared.llm import call_llm

logger = logging.getLogger(__name__)


def _compute_weighted_score(category_scores: dict[str, int]) -> float:
    """Compute weighted average from per-category scores."""
    total = 0.0
    weight_sum = 0.0
    for cat, weight in SCORING_CATEGORIES.items():
        score = category_scores.get(cat, 0)
        total += score * weight
        weight_sum += weight
    return round(total / weight_sum, 1) if weight_sum > 0 else 0.0


def score_papers(papers: list[dict], topics=None) -> list[dict]:
    """Score papers in batches using multi-category LLM scoring.

    Each paper gets a score (1-10) per category, then a weighted average
    is computed as the final score.

    Args:
        papers: List of paper dicts with 'title' and 'abstract'.
        topics: Interest areas for scoring context. Defaults to config TOPICS.

    Returns:
        Same list with 'score' (float), 'category_scores' (dict),
        and 'category' (str) added to each paper.
    """
    # TOPICS is list of (query, weight) tuples; extract just the query strings
    raw = topics or TOPICS
    topic_queries = [t[0] if isinstance(t, tuple) else t for t in raw]
    topics_str = "\n".join(f"- {q}" for q in topic_queries)

    categories_str = ", ".join(SCORING_CATEGORIES.keys())
    weights_str = ", ".join(
        f"{cat}: {w}" for cat, w in SCORING_CATEGORIES.items()
    )

    system_prompt = (
        "You are a research paper evaluator. Score each paper across these "
        f"categories (each 1-10): {categories_str}.\n\n"
        "Scoring guide:\n"
        "- 8-10: Excellent. Directly addresses the topic, groundbreaking or highly useful.\n"
        "- 5-7: Good. Related and interesting but not core to the user's focus.\n"
        "- 1-4: Low. Tangentially related or not useful.\n\n"
        "Use the FULL range. Not everything is a 5.\n\n"
        f"User's interest areas:\n{topics_str}\n\n"
        f"Category weights for context (you don't compute these): {weights_str}"
    )

    scored = []
    for i in range(0, len(papers), SCORE_BATCH_SIZE):
        batch = papers[i : i + SCORE_BATCH_SIZE]
        batch_text = ""
        for j, p in enumerate(batch):
            abstract = (p.get("abstract") or "No abstract available.")[:500]
            batch_text += f"\n[{j}] Title: {p['title']}\nAbstract: {abstract}\n"

        example_scores = {cat: 7 for cat in SCORING_CATEGORIES}
        example_scores["relevance"] = 9
        paper_cats_str = ", ".join(PAPER_CATEGORIES)
        example = json.dumps(
            [{"index": 0, "scores": example_scores, "category": PAPER_CATEGORIES[0]}],
            indent=None,
        )

        prompt = (
            f"Rate each paper below across these dimensions (1-10 each): "
            f"{categories_str}.\n"
            f"Also assign a category (one of: {paper_cats_str}).\n"
            f"Respond ONLY with valid JSON array, no other text.\n"
            f"Format: {example}\n"
            f"\nPapers:{batch_text}"
        )

        try:
            results = call_llm(prompt, system=system_prompt, expect_json=True)
            for entry in results:
                idx = entry.get("index", 0)
                if 0 <= idx < len(batch):
                    cat_scores = entry.get("scores", {})
                    batch[idx]["category_scores"] = cat_scores
                    batch[idx]["score"] = _compute_weighted_score(cat_scores)
                    batch[idx]["category"] = entry.get("category", "llm")
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Scoring batch {i // SCORE_BATCH_SIZE} failed: {e}")
            for p in batch:
                p.setdefault("score", 0.0)
                p.setdefault("category_scores", {})
                p.setdefault("category", "llm")

        scored.extend(batch)

    scored_count = sum(1 for p in scored if p.get("score", 0) > 0)
    logger.info(f"Scored {scored_count}/{len(scored)} papers successfully")
    return scored


def filter_by_threshold(papers: list[dict], min_score: float = 5.0) -> list[dict]:
    """Keep only papers with weighted score >= min_score."""
    filtered = [p for p in papers if p.get("score", 0) >= min_score]
    logger.info(f"Filtered: {len(filtered)}/{len(papers)} papers passed threshold {min_score}")
    return filtered
