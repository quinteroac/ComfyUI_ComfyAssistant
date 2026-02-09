"""
Load system context (system_context/*.md) and user context (user_context/, DB) for prompt injection.

Final context = system_context + user_context + skills (same injection mechanism).
Phase 1: skills are manual (file-based). Token budget applied so we don't blow context.
"""

import os
from typing import Any

from user_context_store import (
    get_user_context_path,
    ensure_user_context_dirs,
    ensure_environment_dirs,
    get_rules,
    get_preferences,
)

# Max total characters for the "user context" block in the system message
MAX_USER_CONTEXT_CHARS = 4000
# If total skills content is under this, include full text; else use summaries
MAX_SKILLS_FULL_CHARS = 1500
# Max chars for SOUL + goals combined (so skills get remaining budget)
MAX_NARRATIVE_CHARS = 1200


def _read_file_utf8(path: str) -> str:
    """Read file as UTF-8; return empty string if missing or error."""
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read().strip()
    except (OSError, UnicodeDecodeError):
        return ""


def _parse_skill_md(content: str) -> tuple[dict[str, str], str]:
    """
    Parse SKILL.md per Agent Skills standard (https://code.claude.com/docs/en/skills).
    Frontmatter is YAML between --- and ---. Returns (frontmatter_dict, body).
    """
    fm: dict[str, str] = {}
    body = content.strip()
    if body.startswith("---"):
        rest = body[3:].lstrip("\n")
        end = rest.find("\n---")
        if end >= 0:
            fm_block = rest[:end].strip()
            body = rest[end + 4:].strip()
            for line in fm_block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip().lower()] = v.strip().strip("'\"").strip()
    return (fm, body)


def load_system_context(system_context_dir: str) -> str:
    """
    Load system context from a directory of .md files (e.g. system_context/).
    Load order: (1) top-level .md files in sorted order, (2) skills/*.md in sorted order.
    Skips README.md. Returns the combined string for the base system prompt; empty if dir missing or no .md files.
    """
    if not os.path.isdir(system_context_dir):
        return ""
    parts = []
    for name in sorted(os.listdir(system_context_dir)):
        if name == "README.md" or name == "skills":
            continue
        if not name.endswith(".md"):
            continue
        path = os.path.join(system_context_dir, name)
        if not os.path.isfile(path):
            continue
        content = _read_file_utf8(path)
        if content:
            parts.append(content)
    skills_dir = os.path.join(system_context_dir, "skills")
    if os.path.isdir(skills_dir):
        for name in sorted(os.listdir(skills_dir)):
            skill_dir = os.path.join(skills_dir, name)
            if not os.path.isdir(skill_dir):
                continue
            skill_md = os.path.join(skill_dir, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            content = _read_file_utf8(skill_md)
            if not content:
                continue
            _fm, body = _parse_skill_md(content)
            if body:
                parts.append(body)
    return "\n\n".join(parts) if parts else ""


def _first_paragraph_or_lines(text: str, max_lines: int = 2) -> str:
    """Return first paragraph or first max_lines lines for summary."""
    lines = text.strip().splitlines()
    if not lines:
        return ""
    # First paragraph (until blank line)
    for i, line in enumerate(lines):
        if not line.strip():
            return "\n".join(lines[:i]).strip() or lines[0]
    # Or first N lines
    return "\n".join(lines[:max_lines]).strip()


def load_skills() -> list[tuple[str, str, bool]]:
    """
    Load skills from user_context/skills/ per Agent Skills standard.
    Each skill is a directory with SKILL.md (YAML frontmatter + body). Legacy flat .md files are still supported.
    Returns list of (slug, content_or_summary, is_full).
    """
    ensure_user_context_dirs()
    root = get_user_context_path()
    skills_dir = os.path.join(root, "skills")
    if not os.path.isdir(skills_dir):
        return []

    collected: list[tuple[str, str]] = []

    for name in sorted(os.listdir(skills_dir)):
        path = os.path.join(skills_dir, name)
        if os.path.isdir(path):
            skill_md = os.path.join(path, "SKILL.md")
            if not os.path.isfile(skill_md):
                continue
            raw = _read_file_utf8(skill_md)
            if not raw:
                continue
            fm, body = _parse_skill_md(raw)
            if not body:
                continue
            slug = (fm.get("name") or name).strip().lower().replace(" ", "-")
            collected.append((slug, body))
        elif name.endswith(".md") and os.path.isfile(path):
            content = _read_file_utf8(path)
            if content:
                slug = name[:-3]
                collected.append((slug, content))

    total_len = sum(len(c) for _, c in collected)
    use_full = total_len <= MAX_SKILLS_FULL_CHARS
    return [
        (slug, content if use_full else _first_paragraph_or_lines(content, 2), use_full)
        for slug, content in collected
    ]


def load_environment_summary() -> str:
    """Load cached environment summary text for system prompt injection.

    Returns brief text like "87 custom node packages, 523 node types, 150 models."
    Returns empty string if no cached scan exists.
    """
    try:
        from environment_scanner import get_environment_summary
        env_dir = ensure_environment_dirs()
        return get_environment_summary(env_dir)
    except Exception:
        return ""


def load_user_context() -> dict[str, Any]:
    """
    Load full user context for prompt injection.
    Returns dict: rules, soul_text, goals_text, preferences, skills (list of {slug, text, is_full}).
    """
    root = get_user_context_path()
    soul_path = os.path.join(root, "SOUL.md")
    goals_path = os.path.join(root, "goals.md")

    rules = get_rules()
    preferences = get_preferences()
    soul_text = _read_file_utf8(soul_path)
    goals_text = _read_file_utf8(goals_path)
    skills_tuples = load_skills()

    skills = [
        {"slug": slug, "text": text, "is_full": is_full}
        for slug, text, is_full in skills_tuples
    ]

    return {
        "rules": rules,
        "soul_text": soul_text,
        "goals_text": goals_text,
        "preferences": preferences,
        "skills": skills,
    }
