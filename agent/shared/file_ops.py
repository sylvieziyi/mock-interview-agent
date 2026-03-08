"""Shared file operations — download, organize, slugify."""

import logging
import re
from pathlib import Path

import requests

logger = logging.getLogger(__name__)

# Shared session for connection pooling
_session = requests.Session()
_session.headers.update({"User-Agent": "Junnie-Crew-Agent/1.0"})


def slugify(text: str, max_length: int = 60) -> str:
    """Convert text to a filesystem-safe slug."""
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text).strip("_")
    return text[:max_length]


def download_file(url: str, save_path: Path, timeout: int = 60) -> bool:
    """Download a file from a URL to a local path.

    Args:
        url: URL to download from.
        save_path: Local path to save the file.
        timeout: Request timeout in seconds.

    Returns:
        True if downloaded successfully.
    """
    if save_path.exists():
        logger.info(f"Already exists: {save_path.name}")
        return True

    save_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        resp = _session.get(url, timeout=timeout)
        resp.raise_for_status()
        save_path.write_bytes(resp.content)
        logger.info(f"Downloaded: {save_path.name} ({len(resp.content) // 1024} KB)")
        return True
    except Exception as e:
        logger.error(f"Download failed for {url}: {e}")
        return False


def ensure_dir(path: Path) -> Path:
    """Create directory if it doesn't exist, return the path."""
    path.mkdir(parents=True, exist_ok=True)
    return path
