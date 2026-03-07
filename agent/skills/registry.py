"""Skill registry: loads skill definitions and maps them to tool functions."""

import logging
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


class Skill:
    """A skill loaded from a markdown definition file."""

    def __init__(self, name: str, definition: str, tools: dict[str, Callable]):
        self.name = name
        self.definition = definition  # raw markdown content
        self.tools = tools  # mapping of tool_name -> callable

    def __repr__(self):
        return f"Skill({self.name}, tools={list(self.tools.keys())})"


class SkillRegistry:
    """Loads skill .md files and maps skill names to tool functions."""

    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.skills: dict[str, Skill] = {}

    def register(self, skill_name: str, tools: dict[str, Callable]):
        """Register tool functions for a skill. Call this after loading definitions."""
        md_path = self.skills_dir / f"{skill_name}.md"
        if not md_path.exists():
            raise FileNotFoundError(f"Skill definition not found: {md_path}")

        definition = md_path.read_text()
        self.skills[skill_name] = Skill(
            name=skill_name,
            definition=definition,
            tools=tools,
        )
        logger.info(f"Registered skill: {skill_name} with tools: {list(tools.keys())}")

    def get_skill(self, skill_name: str) -> Skill:
        """Get a registered skill by name."""
        if skill_name not in self.skills:
            raise KeyError(f"Skill not registered: {skill_name}")
        return self.skills[skill_name]

    def get_all_definitions(self) -> str:
        """Return all skill definitions as a single string for the planner prompt."""
        parts = []
        for skill in self.skills.values():
            parts.append(skill.definition)
        return "\n---\n".join(parts)

    def list_skills(self) -> list[str]:
        """Return list of registered skill names."""
        return list(self.skills.keys())

    def execute_skill(self, skill_name: str, tool_name: str, **kwargs):
        """Execute a specific tool within a skill."""
        skill = self.get_skill(skill_name)
        if tool_name not in skill.tools:
            raise KeyError(f"Tool '{tool_name}' not found in skill '{skill_name}'")
        logger.info(f"Executing {skill_name}.{tool_name}")
        return skill.tools[tool_name](**kwargs)
