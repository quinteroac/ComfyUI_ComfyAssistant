"""
Load system context (system_context/*.md) and user context (user_context/, DB) for prompt injection.

Final context = system_context + user_context + skills (same injection mechanism).
Phase 1: skills are manual (file-based). Token budget applied so we don't blow context.
"""

import os
import re
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
PERSONA_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,61}[a-z0-9])?$")


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


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """
    Parse simple YAML frontmatter and markdown body.
    Supports only `key: value` pairs, which is enough for SOUL.md metadata.
    """
    fm: dict[str, str] = {}
    body = content.strip()
    if not body.startswith("---"):
        return (fm, body)

    rest = body[3:].lstrip("\n")
    end = rest.find("\n---")
    if end < 0:
        return ({}, "")

    fm_block = rest[:end].strip()
    body = rest[end + 4:].strip()

    for line in fm_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        fm[key.strip().lower()] = value.strip().strip("'\"").strip()

    return (fm, body)


def _parse_persona_soul(raw: str) -> dict[str, str] | None:
    """
    Parse persona SOUL.md and enforce required metadata:
    Name, Description, Provider + non-empty markdown body.
    """
    frontmatter, body = _parse_frontmatter(raw)
    name = (frontmatter.get("name") or "").strip()
    description = (frontmatter.get("description") or "").strip()
    provider = (frontmatter.get("provider") or "").strip()

    if not name or not description or not provider or not body.strip():
        return None

    return {
        "name": name,
        "description": description,
        "provider": provider,
        "body": body.strip(),
    }


def _is_valid_persona_slug(slug: str) -> bool:
    return bool(PERSONA_SLUG_RE.fullmatch((slug or "").strip()))


def _load_active_persona(root: str, preferences: dict[str, Any]) -> dict[str, str] | None:
    """
    Load user_context/personas/<slug>/SOUL.md for the active persona when configured.

    Returns persona metadata + body when valid and provider exists, else None.
    """
    raw_slug = preferences.get("active_persona")
    if not isinstance(raw_slug, str):
        return None
    slug = raw_slug.strip().lower()
    if not _is_valid_persona_slug(slug):
        return None

    persona_dir = os.path.join(root, "personas", slug)
    soul_path = os.path.join(persona_dir, "SOUL.md")
    if not os.path.isdir(persona_dir) or not os.path.isfile(soul_path):
        return None

    parsed = _parse_persona_soul(_read_file_utf8(soul_path))
    if not parsed:
        return None

    try:
        from provider_store import get_provider_by_name
        if not get_provider_by_name(parsed["provider"]):
            return None
    except Exception:
        return None

    return {"slug": slug, **parsed}


def load_system_context(system_context_dir: str) -> str:
    """
    Load system context from a directory of .md files (e.g. system_context/).
    Load order: (1) top-level .md files in sorted order, (2) skills/*.md in sorted order.
    Skips README.md. All skills are included (including model-specific ones);
    smart truncation compresses later sections to headers when over budget,
    so model skills appear as a lightweight index the LLM can reference.
    Returns the combined string for the base system prompt; empty if dir missing or no .md files.
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


def list_system_model_skills(system_context_dir: str) -> list[dict[str, str]]:
    """
    List system-context skills that are model-specific (folder name contains "model_").
    Returns list of {slug, name}; slug is the folder name (e.g. 09_model_flux).
    """
    result: list[dict[str, str]] = []
    skills_dir = os.path.join(system_context_dir, "skills")
    if not os.path.isdir(skills_dir):
        return result
    for name in sorted(os.listdir(skills_dir)):
        if "model_" not in name:
            continue
        skill_dir = os.path.join(skills_dir, name)
        if not os.path.isdir(skill_dir):
            continue
        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        content = _read_file_utf8(skill_md)
        if not content:
            continue
        fm, body = _parse_skill_md(content)
        name_display = (fm.get("name") or name).strip()
        result.append({"slug": name, "name": name_display})
    return result


def get_system_model_skill(system_context_dir: str, slug: str) -> dict[str, str] | None:
    """
    Load a single system model skill by slug (folder name, e.g. 09_model_flux).
    Returns {slug, name, content} or None if not found.
    """
    if not slug or not slug.strip():
        return None
    slug = slug.strip()
    if ".." in slug or "/" in slug or "\\" in slug:
        return None
    skills_dir = os.path.join(system_context_dir, "skills")
    skill_dir = os.path.join(skills_dir, slug)
    skill_md = os.path.join(skill_dir, "SKILL.md")
    if not os.path.isdir(skill_dir) or not os.path.isfile(skill_md):
        return None
    content = _read_file_utf8(skill_md)
    if not content:
        return None
    fm, body = _parse_skill_md(content)
    name_display = (fm.get("name") or slug).strip()
    return {"slug": slug, "name": name_display, "content": body.strip()}


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
    Load user context for prompt injection (rules, SOUL, goals, preferences).

    User skills are not loaded here; they are fetched on demand via
    skill_manager.get_skill(slug) when the model calls getUserSkill.
    """
    root = get_user_context_path()
    goals_path = os.path.join(root, "goals.md")

    rules = get_rules()
    preferences = get_preferences()
    persona = _load_active_persona(root, preferences)
    soul_text = persona["body"] if persona else _read_file_utf8(os.path.join(root, "SOUL.md"))
    goals_text = _read_file_utf8(goals_path)

    return {
        "rules": rules,
        "soul_text": soul_text,
        "persona": persona,
        "goals_text": goals_text,
        "preferences": preferences,
    }
