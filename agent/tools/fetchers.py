"""Paper fetchers — arXiv only.

Results are sorted by relevance to the query and filtered by time range.
"""

import logging
import socket
import time
from datetime import datetime, timedelta

import arxiv

from agent.config import PAPER_TIME_RANGE_DAYS

ARXIV_TIMEOUT = 30  # seconds per request

logger = logging.getLogger(__name__)


def search_arxiv(topics: list[tuple[str, int]], base_results: int = 30) -> list[dict]:
    """Search arXiv for papers matching topic keywords within the configured time range.

    Args:
        topics: List of (query, weight) tuples. max_results = base_results * weight.
        base_results: Base fetch count, multiplied by each topic's weight.
    """
    papers = []
    seen_ids = set()
    cutoff_date = datetime.now() - timedelta(days=PAPER_TIME_RANGE_DAYS)
    client = arxiv.Client()

    for topic, weight in topics:
        max_results = base_results * weight
        try:
            search = arxiv.Search(
                query=topic,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.Relevance,
            )
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(ARXIV_TIMEOUT)
            try:
                results = list(client.results(search))
            finally:
                socket.setdefaulttimeout(old_timeout)
            for result in results:
                # Filter by time range
                if result.published.replace(tzinfo=None) < cutoff_date:
                    continue

                arxiv_id = result.entry_id.split("/abs/")[-1]
                if arxiv_id in seen_ids:
                    continue
                seen_ids.add(arxiv_id)
                papers.append({
                    "title": result.title,
                    "abstract": result.summary,
                    "url": result.entry_id,
                    "pdf_url": result.pdf_url,
                    "arxiv_id": arxiv_id,
                    "source": "arxiv",
                    "published": result.published.isoformat(),
                })
            time.sleep(1)  # be polite to arXiv API
        except Exception as e:
            logger.error(f"arXiv search failed for topic '{topic}': {e}")

    logger.info(f"arXiv: found {len(papers)} papers")
    return papers
