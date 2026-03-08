"""Skill registry — auto-discovers and manages skills.

Scans the skills/ directory for subdirectories containing:
  - skill.md    — LLM-readable description (for the planner)
  - executor.py — execution logic with an execute(context, dry_run) function

Skills are discovered automatically. No manual registration needed.
"""

import importlib
import logging
from pathlib import Path

from agent.context import ContextStore

logger = logging.getLogger(__name__)

SKILLS_DIR = Path(__file__).parent


class SkillInfo:
    """Metadata and executor for a discovered skill."""

    def __init__(self, name: str, description: str, executor_module):
        self.name = name
        self.description = description  # raw markdown from skill.md
        self.executor = executor_module  # module with execute(context, dry_run)

    def __repr__(self):
        return f"Skill({self.name})"


class SkillRegistry:
    """Auto-discovers skills from subdirectories of the skills/ folder."""

    def __init__(self):
        self.skills: dict[str, SkillInfo] = {}
        self._discover()

    def _discover(self):
        """Scan skills/ for subdirectories with skill.md + executor.py."""
        for path in sorted(SKILLS_DIR.iterdir()):
            if not path.is_dir():
                continue
            if path.name.startswith("_"):
                continue

            skill_md = path / "skill.md"
            executor_py = path / "executor.py"

            if skill_md.exists() and executor_py.exists():
                try:
                    description = skill_md.read_text()
                    module = importlib.import_module(
                        f"agent.skills.{path.name}.executor"
                    )
                    self.skills[path.name] = SkillInfo(
                        name=path.name,
                        description=description,
                        executor_module=module,
                    )
                    logger.info(f"Discovered skill: {path.name}")
                except Exception as e:
                    logger.error(f"Failed to load skill '{path.name}': {e}")

    def get_all_descriptions(self) -> str:
        """Return all skill descriptions concatenated (for the planner prompt)."""
        parts = []
        for skill in self.skills.values():
            parts.append(skill.description)
        return "\n---\n".join(parts)

    def list_skills(self) -> list[str]:
        """Return names of all discovered skills."""
        return list(self.skills.keys())

    def execute_skill(self, name: str, context: ContextStore, dry_run: bool = False):
        """Execute a skill by name."""
        if name not in self.skills:
            raise KeyError(f"Skill not found: {name}. Available: {self.list_skills()}")

        skill = self.skills[name]
        logger.info(f"Executing skill: {name}")
        skill.executor.execute(context, dry_run=dry_run)

    def has_skill(self, name: str) -> bool:
        """Check if a skill exists."""
        return name in self.skills
