"""Generic planner — selects which skill(s) to run for a given goal.

The planner reads all skill descriptions (from skill.md files) and asks
the LLM to select the most appropriate skill(s) for the user's goal.
It does NOT plan individual steps — each skill handles its own pipeline.
"""

import json
import logging

from agent.context import ContextStore
from agent.shared.llm import call_llm
from agent.skills.registry import SkillRegistry

logger = logging.getLogger(__name__)

PLANNER_SYSTEM_PROMPT = """\
You are a planning agent. Given a user's goal and a set of available skills,
select which skill(s) should be executed to accomplish the goal.

Rules:
- Select only skills that are relevant to the goal
- Most goals only need 1 skill
- Output a JSON array of skill names to execute, in order
- If no skill matches, return an empty array []

Respond ONLY with a valid JSON array of strings, no other text.
Example: ["ai_paper_agent"]
"""


def select_skills(
    registry: SkillRegistry,
    goal: str,
    context: ContextStore | None = None,
) -> list[str]:
    """Use the LLM to select which skill(s) to run for a given goal.

    Args:
        registry: The skill registry with discovered skills.
        goal: The user's high-level goal.
        context: Optional context for session history.

    Returns:
        Ordered list of skill names to execute.
    """
    skills_context = registry.get_all_descriptions()
    available = registry.list_skills()

    prompt = (
        f"Available skills:\n\n{skills_context}\n\n"
        f"---\n\n"
        f"User's goal: {goal}\n\n"
        f"Which skill(s) should run? Respond with a JSON array of skill names."
    )

    try:
        result = call_llm(prompt, system=PLANNER_SYSTEM_PROMPT, expect_json=True)

        # Validate that all returned skill names actually exist
        if isinstance(result, list):
            valid = [s for s in result if s in available]
            if valid:
                logger.info(f"Planner selected skills: {valid}")
                if context:
                    context.log_step("planner", "success", f"Selected: {valid}")
                return valid

        logger.warning(f"Planner returned invalid skills: {result}")
    except Exception as e:
        logger.warning(f"Planner failed ({e}), using fallback")

    # Fallback: keyword matching
    return _fallback_select(goal, available, context)


def _fallback_select(
    goal: str,
    available: list[str],
    context: ContextStore | None = None,
) -> list[str]:
    """Fallback skill selection using keyword matching."""
    goal_lower = goal.lower()

    # Simple keyword mapping
    keyword_map = {
        "ai_paper_agent": ["paper", "research", "arxiv", "digest", "academic", "ai papers"],
    }

    selected = []
    for skill_name in available:
        keywords = keyword_map.get(skill_name, [skill_name.replace("_", " ")])
        if any(kw in goal_lower for kw in keywords):
            selected.append(skill_name)

    # If nothing matched, run all skills (best effort)
    if not selected:
        selected = available
        logger.warning(f"No keyword match for goal, running all skills: {selected}")
    else:
        logger.info(f"Fallback selected skills: {selected}")

    if context:
        context.log_step("planner", "fallback", f"Selected: {selected}")

    return selected
