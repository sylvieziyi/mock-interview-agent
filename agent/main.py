"""Junnie-Crew Agent — generic entry point.

Usage:
    python -m agent.main                          # default goal, uses planner
    python -m agent.main --dry-run                 # no LLM/download/email
    python -m agent.main --goal "find AI papers"   # custom goal
    python -m agent.main --skill ai_paper_agent    # skip planner, run directly
"""

import argparse
import logging
import sys
from datetime import datetime

from agent.config import LOG_DIR
from agent.context import ContextStore
from agent.planner import fallback_select, select_skills
from agent.shared.llm import is_ollama_running
from agent.skills.registry import SkillRegistry

logger = logging.getLogger("agent")

DEFAULT_GOAL = "Collect today's best AI papers, filter for quality, summarize, download, and send email digest"


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


def main():
    parser = argparse.ArgumentParser(description="Junnie-Crew Agent")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without LLM calls, downloads, or email sending",
    )
    parser.add_argument(
        "--goal",
        type=str,
        default=DEFAULT_GOAL,
        help="The goal for the agent to accomplish",
    )
    parser.add_argument(
        "--skill",
        type=str,
        default=None,
        help="Skip planner and run a specific skill directly",
    )
    args = parser.parse_args()

    setup_logging()
    logger.info(f"=== Junnie-Crew Agent started at {datetime.now().isoformat()} ===")

    if args.dry_run:
        logger.info("Running in DRY RUN mode")

    # Initialize context
    context = ContextStore()
    logger.info(f"Session: {context.session_id}")

    # Discover skills
    registry = SkillRegistry()
    available = registry.list_skills()
    logger.info(f"Available skills: {available}")

    if not available:
        logger.error("No skills found. Add skills to agent/skills/")
        return

    # Pre-flight check: ensure Ollama is reachable (skip in dry-run)
    if not args.dry_run and not is_ollama_running():
        logger.error("Ollama is not running or model is not available. Start Ollama first.")
        return

    # Select skills to run
    if args.skill:
        # Direct skill execution (bypass planner)
        if not registry.has_skill(args.skill):
            logger.error(f"Skill '{args.skill}' not found. Available: {available}")
            return
        skills_to_run = [args.skill]
        logger.info(f"Direct execution: {args.skill}")
    elif args.dry_run:
        # In dry-run, skip the planner LLM call too
        skills_to_run = fallback_select(args.goal, available)
        logger.info(f"Dry-run skill selection: {skills_to_run}")
    else:
        # Use the LLM planner
        skills_to_run = select_skills(registry, args.goal, context)

    # Execute selected skills
    for skill_name in skills_to_run:
        try:
            registry.execute_skill(skill_name, context, dry_run=args.dry_run)
        except Exception as e:
            logger.error(f"Skill '{skill_name}' failed: {e}")
            context.log_step(skill_name, "error", str(e))

    # Save session
    context.save_session()
    logger.info(f"=== Done — session saved ===")


if __name__ == "__main__":
    main()
