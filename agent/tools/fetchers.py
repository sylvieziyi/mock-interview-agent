"""Paper fetchers for arXiv, HuggingFace, Papers With Code, and Semantic Scholar."""

import logging
import time
from datetime import datetime, timedelta

import arxiv
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Shared session for connection pooling
_session = requests.Session()
_session.headers.update({"User-Agent": "AI-Paper-Agent/1.0"})


def search_arxiv(topics: list[str], max_results: int = 50) -> list[dict]:
    """Search arXiv for recent papers matching topic keywords."""
    papers = []
    seen_ids = set()

    for topic in topics:
        try:
            search = arxiv.Search(
                query=topic,
                max_results=max_results,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending,
            )
            client = arxiv.Client()
            for result in client.results(search):
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


def search_huggingface() -> list[dict]:
    """Fetch today's trending papers from HuggingFace daily papers page."""
    papers = []
    try:
        resp = _session.get("https://huggingface.co/papers", timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # HF papers page uses article tags or specific div structures
        for article in soup.select("article"):
            title_el = article.select_one("h3")
            if not title_el:
                continue

            title = title_el.get_text(strip=True)
            link_el = article.select_one("a[href*='/papers/']")
            if not link_el:
                continue

            paper_url = "https://huggingface.co" + link_el["href"]

            # Try to extract arxiv ID from the URL
            arxiv_id = None
            href = link_el["href"]
            if "/papers/" in href:
                arxiv_id = href.split("/papers/")[-1]

            papers.append({
                "title": title,
                "abstract": "",  # HF page may not show full abstract
                "url": paper_url,
                "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else "",
                "arxiv_id": arxiv_id or "",
                "source": "huggingface",
                "published": datetime.now().isoformat(),
            })
    except Exception as e:
        logger.error(f"HuggingFace fetch failed: {e}")

    logger.info(f"HuggingFace: found {len(papers)} papers")
    return papers


def search_papers_with_code(max_results: int = 30) -> list[dict]:
    """Fetch trending papers from Papers With Code API."""
    papers = []
    try:
        resp = _session.get(
            "https://paperswithcode.com/api/v1/papers/",
            params={"ordering": "-published", "items_per_page": max_results},
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        for item in data.get("results", []):
            arxiv_id = item.get("arxiv_id", "") or ""
            papers.append({
                "title": item.get("title", ""),
                "abstract": item.get("abstract", ""),
                "url": item.get("url_abs", "") or item.get("paper_url", ""),
                "pdf_url": item.get("url_pdf", ""),
                "arxiv_id": arxiv_id,
                "source": "papers_with_code",
                "published": item.get("published", ""),
            })
    except Exception as e:
        logger.error(f"Papers With Code fetch failed: {e}")

    logger.info(f"Papers With Code: found {len(papers)} papers")
    return papers


def search_semantic_scholar(topics: list[str], max_results: int = 20) -> list[dict]:
    """Search Semantic Scholar for recent papers matching topics."""
    papers = []
    seen_ids = set()
    # Only look at papers from the last 7 days
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    for topic in topics:
        try:
            resp = _session.get(
                "https://api.semanticscholar.org/graph/v1/paper/search",
                params={
                    "query": topic,
                    "limit": max_results,
                    "fields": "title,abstract,externalIds,url,publicationDate",
                    "publicationDateOrYear": f"{week_ago}:",
                },
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

            for item in data.get("data", []):
                paper_id = item.get("paperId", "")
                if paper_id in seen_ids:
                    continue
                seen_ids.add(paper_id)

                ext_ids = item.get("externalIds") or {}
                arxiv_id = ext_ids.get("ArXiv", "")
                doi = ext_ids.get("DOI", "")

                papers.append({
                    "title": item.get("title", ""),
                    "abstract": item.get("abstract", "") or "",
                    "url": item.get("url", ""),
                    "pdf_url": f"https://arxiv.org/pdf/{arxiv_id}" if arxiv_id else "",
                    "arxiv_id": arxiv_id,
                    "doi": doi,
                    "source": "semantic_scholar",
                    "published": item.get("publicationDate", ""),
                })
            time.sleep(1)  # respect rate limits
        except Exception as e:
            logger.error(f"Semantic Scholar search failed for topic '{topic}': {e}")

    logger.info(f"Semantic Scholar: found {len(papers)} papers")
    return papers
