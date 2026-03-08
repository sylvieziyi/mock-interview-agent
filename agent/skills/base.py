"""Base skill contract.

All skills must implement the SkillExecutor protocol:
- execute(context, dry_run) -> dict with at least a 'status' key.
"""

from typing import Any, Protocol

from agent.context import ContextStore


class SkillExecutor(Protocol):
    """Protocol that all skill executor modules must satisfy."""

    def execute(self, context: ContextStore, dry_run: bool = False) -> dict[str, Any]:
        """Run the skill pipeline.

        Args:
            context: Shared context store for memory management.
            dry_run: If True, skip side effects (LLM calls, downloads, email).

        Returns:
            Result dict with at least 'status' ('success' | 'error') key.
        """
        ...
