"""Qwen-based planning agent that loads skills and creates execution plans."""

import json
import logging

import requests

from agent.config import OLLAMA_BASE_URL, OLLAMA_MODEL
from agent.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """\
You are a planning agent. You receive a goal and a set of available skills.
Your job is to create an ordered execution plan using only the available skills.

Rules:
- Use only the skills listed below
- Output a JSON array of steps
- Each step has: skill_name, reason (why this step is needed)
- Order matters — each step can use output from previous steps
- Be concise

Respond ONLY with a valid JSON array, no other text.
Format: [{"step": 1, "skill_name": "...", "reason": "..."}]
"""


def create_plan(registry: SkillRegistry, goal: str) -> list[dict]:
    """Use Qwen to create an execution plan from available skills.

    Args:
        registry: The skill registry with loaded skill definitions.
        goal: The high-level goal to accomplish.

    Returns:
        List of plan steps, each with 'skill_name' and 'reason'.
    """
    skills_context = registry.get_all_definitions()

    prompt = (
        f"Available skills:\n\n{skills_context}\n\n"
        f"---\n\n"
        f"Goal: {goal}\n\n"
        f"Create an execution plan:"
    )

    try:
        resp = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "system": PLANNER_SYSTEM_PROMPT,
                "stream": False,
            },
            timeout=300,
        )
        resp.raise_for_status()
        response_text = resp.json().get("response", "").strip()

        # Handle markdown code blocks
        if response_text.startswith("```"):
            response_text = response_text.split("\n", 1)[-1].rsplit("```", 1)[0]

        plan = json.loads(response_text)
        logger.info(f"Plan created with {len(plan)} steps")
        for step in plan:
            logger.info(f"  Step {step.get('step', '?')}: {step['skill_name']} — {step['reason']}")
        return plan

    except (json.JSONDecodeError, requests.RequestException) as e:
        logger.warning(f"Planner failed ({e}), using default plan")
        return get_default_plan()


def get_default_plan() -> list[dict]:
    """Fallback plan if Qwen planner fails."""
    return [
        {"step": 1, "skill_name": "paper_discovery", "reason": "Fetch papers from all sources"},
        {"step": 2, "skill_name": "paper_evaluation", "reason": "Score and filter by relevance"},
        {"step": 3, "skill_name": "paper_summarization", "reason": "Summarize kept papers"},
        {"step": 4, "skill_name": "file_management", "reason": "Download PDFs and organize"},
        {"step": 5, "skill_name": "notification", "reason": "Send email digest"},
    ]
