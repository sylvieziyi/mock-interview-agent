"""AI Paper Agent skill executor.

Orchestrates the full paper collection pipeline:
  fetch → dedup → pre-filter (signals) → score (LLM) → filter → summarize → download → notify

Source: arXiv (weighted topic queries with cat: category filters).
Scoring: LLM-based relevance scoring, filtered by threshold, top N selected.

This executor imports reusable tools from agent/tools/ and agent/shared/.
It owns only the pipeline logic, not the tool implementations.
"""

import logging
from datetime import datetime

from agent.config import (
    ARXIV_BASE_RESULTS,
    MAX_FINAL_PAPERS,
    MIN_QUALITY_SCORE,
    PAPERS_DIR,
    TOPICS,
)
from agent.context import ContextStore
from agent.shared.email import send_email
from agent.shared.file_ops import download_file, slugify
from agent.tools.fetchers import (
    search_arxiv,

)
from agent.tools.scorer import filter_by_threshold, prefilter_by_signals, score_papers
from agent.tools.summarizer import summarize_papers

logger = logging.getLogger(__name__)


def execute(context: ContextStore, dry_run: bool = False):
    """Run the AI paper agent pipeline.

    Args:
        context: The shared context store for memory management.
        dry_run: If True, skip LLM calls, downloads, and email.
    """
    logger.info("=== AI Paper Agent: starting ===")

    # --- Step 1: Fetch papers from all sources ---
    papers = _fetch_papers(context)
    if not papers:
        logger.info("No new papers found — done.")
        context.log_step("ai_paper_agent", "completed", "No new papers found")
        return

    # --- Step 2: Pre-filter by open-source signals ---
    papers = prefilter_by_signals(papers)
    context.log_step("prefilter", "success", f"{len(papers)} papers passed signal pre-filter")

    if not papers:
        logger.info("No papers passed signal pre-filter — done.")
        context.log_step("ai_paper_agent", "completed", "No papers passed pre-filter")
        return

    # --- Step 3: LLM score and filter ---
    papers = _score_and_filter(papers, context, dry_run)
    if not papers:
        logger.info("No papers passed quality threshold — done.")
        context.log_step("ai_paper_agent", "completed", "No papers passed threshold")
        return

    # --- Step 3b: Keep only top N papers by score ---
    if len(papers) > MAX_FINAL_PAPERS:
        papers = sorted(papers, key=lambda p: p.get("score", 0), reverse=True)[:MAX_FINAL_PAPERS]
        logger.info(f"Limited to top {MAX_FINAL_PAPERS} papers by score")

    # --- Step 4: Summarize ---
    papers = _summarize(papers, context, dry_run)

    # --- Step 5: Download PDFs ---
    papers = _download(papers, context, dry_run)

    # --- Step 6: Send email digest ---
    _notify(papers, context, dry_run)

    # --- Step 7: Update long-term memory (skip in dry-run) ---
    if not dry_run:
        paper_ids = [
            p.get("arxiv_id") or p.get("doi") or p.get("title", "")
            for p in papers
            if p.get("arxiv_id") or p.get("doi") or p.get("title")
        ]
        context.add_seen_papers(paper_ids)
    else:
        logger.info("[DRY RUN] Skipping long-term memory update")

    context.log_step("ai_paper_agent", "completed", f"Processed {len(papers)} papers")
    context.save_session()

    logger.info(f"=== AI Paper Agent: done — {len(papers)} papers processed ===")


def _fetch_papers(context: ContextStore) -> list[dict]:
    """Fetch from arXiv, then dedup."""
    try:
        all_papers = search_arxiv(TOPICS, ARXIV_BASE_RESULTS)
        logger.info(f"Fetched {len(all_papers)} papers from arXiv")
    except Exception as e:
        logger.error(f"arXiv fetch failed: {e}")
        all_papers = []

    context.log_step("fetch", "success", f"Fetched {len(all_papers)} total papers")
    context.checkpoint("after_fetch")

    # Dedup against long-term memory
    seen = context.get_seen_paper_ids()
    unique = []
    current_ids = set()
    for p in all_papers:
        paper_id = p.get("arxiv_id") or p.get("doi") or p.get("title", "")
        if not paper_id or paper_id in seen or paper_id in current_ids:
            continue
        current_ids.add(paper_id)
        unique.append(p)

    logger.info(f"Dedup: {len(all_papers)} → {len(unique)} unique new papers")
    context.set("papers_raw", unique)
    return unique


def _score_and_filter(
    papers: list[dict], context: ContextStore, dry_run: bool
) -> list[dict]:
    """Score papers with LLM and filter by quality threshold."""
    if dry_run:
        logger.info("[DRY RUN] Skipping LLM scoring — returning all papers unscored")
        for p in papers:
            p["score"] = 0.0
            p["category_scores"] = {}
            p["category"] = "unscored"
        context.log_step("score", "dry_run", f"{len(papers)} papers (unscored)")
        return papers

    papers = score_papers(papers, TOPICS)
    context.checkpoint("after_scoring")

    filtered = filter_by_threshold(papers, MIN_QUALITY_SCORE)
    context.set("papers_scored", filtered)
    context.log_step(
        "score", "success",
        f"Scored {len(papers)} papers, {len(filtered)} passed threshold {MIN_QUALITY_SCORE}"
    )
    return filtered


def _summarize(
    papers: list[dict], context: ContextStore, dry_run: bool
) -> list[dict]:
    """Generate summaries for papers."""
    if dry_run:
        logger.info("[DRY RUN] Skipping LLM summarization")
        for p in papers:
            p["summary"] = f"[DRY RUN] {p.get('abstract', '')[:100]}..."
        context.log_step("summarize", "dry_run", f"Skipped summarization for {len(papers)} papers")
        return papers

    papers = summarize_papers(papers)
    context.set("papers_summarized", papers)
    context.checkpoint("after_summarization")
    context.log_step("summarize", "success", f"Summarized {len(papers)} papers")
    return papers


def _download(
    papers: list[dict], context: ContextStore, dry_run: bool
) -> list[dict]:
    """Download PDFs and organize locally."""
    if dry_run:
        logger.info("[DRY RUN] Skipping PDF downloads")
        for p in papers:
            p["local_path"] = "[DRY RUN]"
        context.log_step("download", "dry_run", "Skipped downloads")
        return papers

    today = datetime.now()
    downloaded = 0

    for paper in papers:
        pdf_url = paper.get("pdf_url", "")
        if not pdf_url:
            paper["local_path"] = ""
            continue

        category = paper.get("category", "other")
        arxiv_id = paper.get("arxiv_id", "").replace("/", "_")
        slug = slugify(paper["title"])
        filename = f"{arxiv_id}_{slug}.pdf" if arxiv_id else f"{slug}.pdf"

        save_dir = (
            PAPERS_DIR
            / str(today.year)
            / f"{today.month:02d}"
            / f"{today.day:02d}"
            / category
        )
        save_path = save_dir / filename

        if download_file(pdf_url, save_path):
            paper["local_path"] = str(save_path)
            downloaded += 1
        else:
            paper["local_path"] = ""

    context.set("papers_downloaded", papers)
    context.log_step("download", "success", f"Downloaded {downloaded}/{len(papers)} PDFs")
    return papers


def _notify(papers: list[dict], context: ContextStore, dry_run: bool):
    """Send email digest."""
    if dry_run:
        logger.info(f"[DRY RUN] Would send digest with {len(papers)} papers:")
        for p in papers:
            score = p.get("score", 0)
            label = f"{score}" if score > 0 else "-"
            logger.info(f"  [{label}] {p['title'][:70]}")
        context.log_step("notify", "dry_run", f"Would send {len(papers)} papers")
        return

    today = datetime.now().strftime("%B %d, %Y")
    html = _build_digest_html(papers, today)
    subject = f"AI Paper Digest - {today} ({len(papers)} papers)"

    success = send_email(subject, html)
    status = "success" if success else "failed"
    context.log_step("notify", status, f"Email with {len(papers)} papers")


def _build_digest_html(papers: list[dict], date_str: str) -> str:
    """Build HTML email body for the paper digest."""
    by_category: dict[str, list[dict]] = {}
    for p in papers:
        cat = p.get("category", "other")
        by_category.setdefault(cat, []).append(p)

    sections = ""
    for category, cat_papers in sorted(by_category.items()):
        items = ""
        for p in cat_papers:
            score = p.get("score", 0)
            cat_scores = p.get("category_scores", {})
            summary = p.get("summary", "No summary available.")
            url = p.get("url", "#")
            local_path = p.get("local_path", "")
            local_info = f'<br><small>Local: <code>{local_path}</code></small>' if local_path else ""

            # Show per-category breakdown
            breakdown = " | ".join(
                f"{k}: {v}" for k, v in cat_scores.items()
            ) if cat_scores else "N/A"

            items += f"""
            <div style="margin-bottom: 16px; padding: 12px; border-left: 3px solid #4A90D9; background: #f8f9fa;">
                <strong><a href="{url}" style="color: #1a73e8; text-decoration: none;">{p['title']}</a></strong>
                <span style="color: #666; font-size: 12px;">[{score}/10]</span>
                <br><span style="color: #999; font-size: 11px;">{breakdown}</span>
                <br><span style="color: #333; font-size: 14px;">{summary}</span>
                {local_info}
            </div>"""

        sections += f"""
        <h2 style="color: #333; border-bottom: 1px solid #ddd; padding-bottom: 4px;">
            {category.upper()}
        </h2>{items}"""

    return f"""
    <html>
    <body style="font-family: -apple-system, Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px;">
        <h1 style="color: #1a73e8;">AI Paper Digest - {date_str}</h1>
        <p style="color: #666;">{len(papers)} curated papers found today.</p>
        {sections}
        <hr style="border: none; border-top: 1px solid #ddd;">
        <p style="color: #999; font-size: 12px;">Generated by Junnie-Crew Agent (Qwen)</p>
    </body>
    </html>"""
