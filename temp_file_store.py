"""Temporary file storage in user_context/temp/ for workflows and prompts.

Used to avoid ARG_MAX limits in CLI providers and to enable file upload
for OpenAI/Anthropic APIs instead of inline JSON.
"""

from __future__ import annotations

import json
import logging
import os
import re
import uuid
from pathlib import Path

import user_context_store

logger = logging.getLogger("ComfyUI_ComfyAssistant.temp_file_store")

TEMP_DIR_NAME = "temp"
MAX_AGE_HOURS_DEFAULT = 24

# Safe filename: alphanumeric, underscore, hyphen, dot for extension
_SAFE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]+(\.[a-zA-Z0-9]+)?$")


def _get_temp_dir() -> Path:
    """Return user_context/temp path and ensure it exists."""
    root = user_context_store.get_user_context_path()
    user_context_store.ensure_user_context_dirs()
    temp_dir = Path(root) / TEMP_DIR_NAME
    temp_dir.mkdir(exist_ok=True)
    return temp_dir


def _is_safe_id(id_or_path: str) -> bool:
    """Ensure id contains no path traversal (.., /, etc.)."""
    if not id_or_path or not isinstance(id_or_path, str):
        return False
    base = id_or_path.strip()
    if ".." in base or "/" in base or "\\" in base:
        return False
    if os.path.basename(base) != base:
        return False
    return bool(_SAFE_ID_PATTERN.match(base))


def write_temp_file(
    content: str | dict,
    prefix: str = "workflow",
    suffix: str = ".json",
) -> str:
    """Write content to user_context/temp/{prefix}_{uuid}{suffix}.

    Args:
        content: String or dict (will be JSON-serialized).
        prefix: Filename prefix (e.g. workflow, prompt).
        suffix: Filename suffix (e.g. .json, .txt).

    Returns:
        Filename (e.g. workflow_a1b2c3.json) for referencing.
    """
    temp_dir = _get_temp_dir()
    safe_prefix = re.sub(r"[^a-zA-Z0-9_-]", "_", prefix)[:64]
    unique = uuid.uuid4().hex[:12]
    filename = f"{safe_prefix}_{unique}{suffix}"

    path = temp_dir / filename

    if isinstance(content, dict):
        text = json.dumps(content, ensure_ascii=False, indent=None)
    else:
        text = str(content)

    path.write_text(text, encoding="utf-8")
    logger.debug("Wrote temp file %s (%d bytes)", filename, len(text))
    return filename


def read_temp_file(path_or_id: str) -> str | dict | None:
    """Read content from user_context/temp/{path_or_id}.

    Args:
        path_or_id: Filename (e.g. workflow_abc123.json).

    Returns:
        Parsed content (dict for .json, str otherwise) or None if missing/invalid.
    """
    if not _is_safe_id(path_or_id):
        return None

    temp_dir = _get_temp_dir()
    path = temp_dir / path_or_id.strip()
    if not path.is_file():
        return None

    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None

    if path.suffix.lower() == ".json":
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    return text


def delete_temp_file(path_or_id: str) -> bool:
    """Delete a temp file. Returns True if deleted, False otherwise."""
    if not _is_safe_id(path_or_id):
        return False

    temp_dir = _get_temp_dir()
    path = temp_dir / path_or_id.strip()
    if not path.is_file():
        return False

    try:
        path.unlink()
        logger.debug("Deleted temp file %s", path_or_id)
        return True
    except OSError:
        return False


def get_temp_file_path(path_or_id: str) -> Path | None:
    """Return absolute Path for a temp file, or None if invalid/missing."""
    if not _is_safe_id(path_or_id):
        return None

    temp_dir = _get_temp_dir()
    path = temp_dir / path_or_id.strip()
    return path if path.is_file() else None


def cleanup_old_temp_files(max_age_hours: int = MAX_AGE_HOURS_DEFAULT) -> int:
    """Delete temp files older than max_age_hours. Returns count deleted."""
    import time

    temp_dir = _get_temp_dir()
    if not temp_dir.exists():
        return 0

    cutoff = time.time() - (max_age_hours * 3600)
    deleted = 0

    for p in temp_dir.iterdir():
        if not p.is_file():
            continue
        try:
            if p.stat().st_mtime < cutoff:
                p.unlink()
                deleted += 1
        except OSError:
            pass

    if deleted:
        logger.info("Cleaned up %d old temp files (older than %d hours)", deleted, max_age_hours)
    return deleted


def is_safe_file_id(id_or_path: str) -> bool:
    """Public check for safe file id (no path traversal)."""
    return _is_safe_id(id_or_path)


__all__ = [
    "write_temp_file",
    "read_temp_file",
    "delete_temp_file",
    "get_temp_file_path",
    "cleanup_old_temp_files",
    "is_safe_file_id",
]
