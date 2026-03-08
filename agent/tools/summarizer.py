"""Paper summarization — reusable domain tool.

Generates concise summaries of papers using the LLM.
Uses shared/llm.py for all LLM calls.
"""

import logging

from agent.shared.llm import call_llm

logger = logging.getLogger(__name__)

SUMMARIZER_SYSTEM_PROMPT = (
    "You are a research paper summarizer. Given a paper's title and abstract, "
    "write exactly 3 concise sentences:\n"
    "1. What problem does it address?\n"
    "2. What is the approach/method?\n"
    "3. What are the key results or contributions?\n"
    "Be specific and technical. No filler words."
)


def summarize_papers(papers: list[dict]) -> list[dict]:
    """Generate a 3-sentence summary for each paper using the LLM.

    Args:
        papers: List of paper dicts with 'title' and 'abstract'.

    Returns:
        Same list with 'summary' field added to each paper.
    """
    for paper in papers:
        abstract = (paper.get("abstract") or "No abstract available.")[:800]
        prompt = f"Title: {paper['title']}\n\nAbstract: {abstract}\n\nSummarize:"

        try:
            paper["summary"] = call_llm(
                prompt, system=SUMMARIZER_SYSTEM_PROMPT
            )
            logger.info(f"Summarized: {paper['title'][:60]}...")
        except Exception as e:
            logger.error(f"Summarization failed for '{paper['title'][:60]}': {e}")
            paper["summary"] = paper.get("abstract", "")[:200] + "..."

    return papers
