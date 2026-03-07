"""PDF downloader and local file organizer."""

import logging
import re
from datetime import datetime
from pathlib import Path

import requests

from agent.config import PAPERS_DIR

logger = logging.getLogger(__name__)


def _slugify(text: str, max_length: int = 60) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text).strip("_")
    return text[:max_length]


def download_pdf(papers: list[dict]) -> list[dict]:
    """Download PDFs for papers that have a pdf_url."""
    today = datetime.now()
    session = requests.Session()
    session.headers.update({"User-Agent": "AI-Paper-Agent/1.0"})

    for paper in papers:
        pdf_url = paper.get("pdf_url", "")
        if not pdf_url:
            logger.warning(f"No PDF URL for: {paper['title'][:60]}")
            paper["local_path"] = ""
            continue

        category = paper.get("category", "other")
        arxiv_id = paper.get("arxiv_id", "").replace("/", "_")
        slug = _slugify(paper["title"])
        filename = f"{arxiv_id}_{slug}.pdf" if arxiv_id else f"{slug}.pdf"

        save_dir = (
            PAPERS_DIR
            / str(today.year)
            / f"{today.month:02d}"
            / f"{today.day:02d}"
            / category
        )
        save_dir.mkdir(parents=True, exist_ok=True)
        save_path = save_dir / filename

        if save_path.exists():
            logger.info(f"Already downloaded: {filename}")
            paper["local_path"] = str(save_path)
            continue

        try:
            resp = session.get(pdf_url, timeout=60)
            resp.raise_for_status()
            save_path.write_bytes(resp.content)
            paper["local_path"] = str(save_path)
            logger.info(f"Downloaded: {filename} ({len(resp.content) // 1024} KB)")
        except Exception as e:
            logger.error(f"Download failed for {pdf_url}: {e}")
            paper["local_path"] = ""

    downloaded = sum(1 for p in papers if p.get("local_path"))
    logger.info(f"Downloaded {downloaded}/{len(papers)} PDFs")
    return papers


def organize_files(papers: list[dict]) -> list[dict]:
    """Ensure all papers are in the correct directory structure.

    This is a no-op if download_pdf already placed them correctly,
    but can be used to reorganize if categories change.
    """
    # Currently download_pdf handles organization directly.
    # This function exists for the skill interface and future reorganization needs.
    return papers
