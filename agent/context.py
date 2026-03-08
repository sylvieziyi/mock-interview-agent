"""Context management for the agent framework.

Three layers of memory:
1. Working Memory  — current task state (in-memory dict, checkpointed to disk)
2. Short-term Memory — current session log (what steps ran, results summary)
3. Long-term Memory — cross-session knowledge (seen papers, user preferences)

TODO: Migrate long-term memory from JSON to SQLite for atomic writes,
      file-locking safety, and efficient lookups at scale.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from agent.config import DATA_DIR

logger = logging.getLogger(__name__)


class ContextStore:
    """Manages agent memory across working, short-term, and long-term layers."""

    def __init__(self, session_id: str | None = None):
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        self.working_memory: dict[str, Any] = {}
        self.session_log: list[dict] = []

        # Paths
        self.checkpoints_dir = DATA_DIR / "checkpoints"
        self.checkpoints_dir.mkdir(parents=True, exist_ok=True)
        self.long_term_path = DATA_DIR / "long_term_memory.json"
        self.session_log_dir = DATA_DIR / "sessions"
        self.session_log_dir.mkdir(parents=True, exist_ok=True)

    # --- Working Memory ---

    def set(self, key: str, value: Any):
        """Store a value in working memory."""
        self.working_memory[key] = value
        logger.debug(f"Context set: {key} = {type(value).__name__}")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a value from working memory."""
        return self.working_memory.get(key, default)

    def clear(self):
        """Clear working memory."""
        self.working_memory.clear()

    # --- Checkpointing ---

    def checkpoint(self, step_name: str):
        """Save current working memory to disk for crash recovery."""
        checkpoint_file = self.checkpoints_dir / f"{self.session_id}_{step_name}.json"
        try:
            serializable = self._make_serializable(self.working_memory)
            checkpoint_file.write_text(json.dumps(serializable, indent=2))
            logger.info(f"Checkpoint saved: {step_name}")
        except Exception as e:
            logger.error(f"Checkpoint failed for {step_name}: {e}")

    def restore_checkpoint(self, step_name: str) -> bool:
        """Restore working memory from a checkpoint."""
        checkpoint_file = self.checkpoints_dir / f"{self.session_id}_{step_name}.json"
        if checkpoint_file.exists():
            self.working_memory = json.loads(checkpoint_file.read_text())
            logger.info(f"Checkpoint restored: {step_name}")
            return True
        return False

    # --- Session Log (Short-term Memory) ---

    def log_step(self, step_name: str, status: str, summary: str, details: dict | None = None):
        """Log a completed step in the session history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "step": step_name,
            "status": status,
            "summary": summary,
            "details": details or {},
        }
        self.session_log.append(entry)

    def save_session(self):
        """Persist the session log to disk."""
        session_file = self.session_log_dir / f"{self.session_id}.json"
        session_file.write_text(json.dumps(self.session_log, indent=2))
        logger.info(f"Session log saved: {session_file}")

    def get_session_summary(self) -> str:
        """Get a compact summary of the current session for LLM context."""
        if not self.session_log:
            return "No steps completed yet."
        lines = []
        for entry in self.session_log:
            lines.append(f"- {entry['step']}: {entry['status']} — {entry['summary']}")
        return "\n".join(lines)

    # --- Long-term Memory ---

    def load_long_term(self) -> dict:
        """Load persistent cross-session memory."""
        if self.long_term_path.exists():
            return json.loads(self.long_term_path.read_text())
        return {"seen_paper_ids": [], "preferences": {}, "stats": {}}

    def save_long_term(self, data: dict):
        """Save persistent cross-session memory."""
        self.long_term_path.write_text(json.dumps(data, indent=2))

    def add_seen_papers(self, paper_ids: list[str]):
        """Add paper IDs to long-term memory for deduplication."""
        lt = self.load_long_term()
        existing = set(lt.get("seen_paper_ids", []))
        existing.update(paper_ids)
        lt["seen_paper_ids"] = sorted(existing)
        self.save_long_term(lt)

    def get_seen_paper_ids(self) -> set:
        """Get all previously seen paper IDs."""
        lt = self.load_long_term()
        return set(lt.get("seen_paper_ids", []))

    def _make_serializable(self, obj: Any) -> Any:
        """Make an object JSON-serializable."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_serializable(item) for item in obj]
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        elif isinstance(obj, Path):
            return str(obj)
        else:
            return str(obj)
