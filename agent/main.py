"""AI Paper Agent — main entry point.

Orchestrates the full daily pipeline:
1. Load skills from definitions
2. Qwen planner creates an execution plan
3. Executor runs each skill step
4. Results flow through: discovery → evaluation → summarization → download → notify
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from agent.config import (
    ARXIV_MAX_RESULTS,
    DATA_DIR,
    LOG_DIR,
    MIN_QUALITY_SCORE,
    SEEN_PAPERS_FILE,
    SEMANTIC_SCHOLAR_MAX_RESULTS,
    SKILLS_DIR,
    TOPICS,
)
from agent.planner import create_plan, get_default_plan
from agent.skills.registry import SkillRegistry
from agent.tools.downloader import download_pdf, organize_files
from agent.tools.fetchers import (
    search_arxiv,
    search_huggingface,
    search_papers_with_code,
    search_semantic_scholar,
)
from agent.tools.notifier import send_email_digest
from agent.tools.scorer import filter_by_threshold, score_papers
from agent.tools.summarizer import summarize_paper

logger = logging.getLogger("agent")


def setup_logging():
    """Configure logging to both file and console."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = LOG_DIR / f"{today}.log"

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout),
        ],
    )


def load_seen_papers() -> set:
    """Load previously seen paper IDs for deduplication."""
    if SEEN_PAPERS_FILE.exists():
        data = json.loads(SEEN_PAPERS_FILE.read_text())
        return set(data)
    return set()


def save_seen_papers(seen: set):
    """Save seen paper IDs to disk."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SEEN_PAPERS_FILE.write_text(json.dumps(sorted(seen), indent=2))


def dedup_papers(papers: list[dict], seen: set) -> list[dict]:
    """Remove duplicates within the batch and against previously seen papers."""
    unique = []
    current_ids = set()

    for p in papers:
        # Use arxiv_id as primary key, fall back to title
        paper_id = p.get("arxiv_id") or p.get("doi") or p.get("title", "")
        if not paper_id or paper_id in seen or paper_id in current_ids:
            continue
        current_ids.add(paper_id)
        unique.append(p)

    logger.info(f"Dedup: {len(papers)} → {len(unique)} unique papers")
    return unique


def build_registry() -> SkillRegistry:
    """Build and register all skills with their tool functions."""
    registry = SkillRegistry(SKILLS_DIR)

    registry.register("paper_discovery", {
        "search_arxiv": lambda: search_arxiv(TOPICS, ARXIV_MAX_RESULTS),
        "search_huggingface": search_huggingface,
        "search_papers_with_code": search_papers_with_code,
        "search_semantic_scholar": lambda: search_semantic_scholar(
            TOPICS, SEMANTIC_SCHOLAR_MAX_RESULTS
        ),
    })

    registry.register("paper_evaluation", {
        "score_papers": score_papers,
        "filter_by_threshold": lambda papers: filter_by_threshold(papers, MIN_QUALITY_SCORE),
    })

    registry.register("paper_summarization", {
        "summarize_paper": summarize_paper,
    })

    registry.register("file_management", {
        "download_pdf": download_pdf,
        "organize_files": organize_files,
    })

    registry.register("notification", {
        "send_email_digest": send_email_digest,
    })

    return registry


def execute_plan(plan: list[dict], registry: SkillRegistry, dry_run: bool = False):
    """Execute the plan step by step, passing data between skills."""
    papers = []
    seen = load_seen_papers()

    for step in plan:
        skill_name = step["skill_name"]
        logger.info(f"--- Step {step.get('step', '?')}: {skill_name} ---")

        if skill_name == "paper_discovery":
            # Run all fetchers and merge results
            all_papers = []
            for tool_name, tool_fn in registry.get_skill(skill_name).tools.items():
                try:
                    result = tool_fn()
                    all_papers.extend(result)
                except Exception as e:
                    logger.error(f"Fetcher {tool_name} failed: {e}")

            papers = dedup_papers(all_papers, seen)

            if not papers:
                logger.warning("No new papers found — stopping pipeline")
                return

        elif skill_name == "paper_evaluation":
            if dry_run:
                logger.info("[DRY RUN] Skipping LLM scoring")
                # In dry run, assign random scores for testing
                for p in papers:
                    p["score"] = 5
                    p["category"] = "llm"
            else:
                papers = score_papers(papers)
            papers = filter_by_threshold(papers, MIN_QUALITY_SCORE)

            if not papers:
                logger.info("No papers passed the quality threshold")
                return

        elif skill_name == "paper_summarization":
            if dry_run:
                logger.info("[DRY RUN] Skipping LLM summarization")
                for p in papers:
                    p["summary"] = f"[DRY RUN] {p.get('abstract', '')[:100]}..."
            else:
                papers = summarize_paper(papers)

        elif skill_name == "file_management":
            if dry_run:
                logger.info("[DRY RUN] Skipping PDF downloads")
                for p in papers:
                    p["local_path"] = "[DRY RUN]"
            else:
                papers = download_pdf(papers)
                papers = organize_files(papers)

        elif skill_name == "notification":
            if dry_run:
                logger.info("[DRY RUN] Skipping email notification")
                logger.info(f"Would send digest with {len(papers)} papers:")
                for p in papers:
                    logger.info(f"  [{p.get('score', '?')}] {p['title'][:70]}")
            else:
                send_email_digest(papers)

        else:
            logger.warning(f"Unknown skill: {skill_name}, skipping")

    # Update seen papers
    for p in papers:
        paper_id = p.get("arxiv_id") or p.get("doi") or p.get("title", "")
        if paper_id:
            seen.add(paper_id)
    save_seen_papers(seen)

    logger.info(f"Pipeline complete. {len(papers)} papers processed.")


def main():
    parser = argparse.ArgumentParser(description="AI Paper Agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without LLM calls, downloads, or email sending",
    )
    parser.add_argument(
        "--no-plan",
        action="store_true",
        help="Skip Qwen planning step, use default pipeline order",
    )
    args = parser.parse_args()

    setup_logging()
    logger.info(f"=== AI Paper Agent started at {datetime.now().isoformat()} ===")

    if args.dry_run:
        logger.info("Running in DRY RUN mode")

    registry = build_registry()
    logger.info(f"Loaded skills: {registry.list_skills()}")

    if args.no_plan or args.dry_run:
        plan = get_default_plan()
        logger.info("Using default plan")
    else:
        plan = create_plan(registry, "Collect today's best AI papers, filter for quality, summarize, download, and send email digest")

    execute_plan(plan, registry, dry_run=args.dry_run)
    logger.info("=== Done ===")


if __name__ == "__main__":
    main()
