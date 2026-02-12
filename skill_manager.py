"""
Skill manager for ComfyUI Assistant.

Handles creation, listing, and deletion of user skills.
Skills are stored as SKILL.md files with YAML frontmatter in
user_context/skills/<slug>/.
"""

import os
import re
import shutil
from typing import Any

from user_context_store import get_user_context_path, ensure_user_context_dirs


def _slugify(name: str) -> str:
    """Convert a skill name to a URL-safe slug."""
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")
    return slug or "unnamed-skill"


def _get_skills_dir() -> str:
    """Return the skills directory path, ensuring it exists."""
    ensure_user_context_dirs()
    return os.path.join(get_user_context_path(), "skills")


def create_skill(name: str, description: str, instructions: str) -> dict[str, Any]:
    """Create a new user skill.

    Args:
        name: Human-readable skill name.
        description: Brief description of what the skill does.
        instructions: Full instructions for the assistant.

    Returns:
        dict with keys: slug, name, description, path.

    Raises:
        ValueError: If name or instructions are empty, or if skill already exists.
    """
    if not name or not name.strip():
        raise ValueError("Skill name is required")
    if not instructions or not instructions.strip():
        raise ValueError("Skill instructions are required")

    name = name.strip()
    description = (description or "").strip()
    instructions = instructions.strip()
    slug = _slugify(name)

    skills_dir = _get_skills_dir()
    skill_dir = os.path.join(skills_dir, slug)

    if os.path.exists(skill_dir):
        raise ValueError(f"Skill '{slug}' already exists. Delete it first or use a different name.")

    os.makedirs(skill_dir, exist_ok=True)

    # Write SKILL.md with YAML frontmatter
    skill_md = os.path.join(skill_dir, "SKILL.md")
    frontmatter = f"---\nname: '{name}'\ndescription: '{description}'\n---\n\n"
    content = frontmatter + instructions

    with open(skill_md, "w", encoding="utf-8") as f:
        f.write(content)

    return {
        "slug": slug,
        "name": name,
        "description": description,
        "path": skill_dir,
    }


def list_skills() -> list[dict[str, Any]]:
    """List all user skills.

    Returns:
        List of dicts with keys: slug, name, description.
    """
    skills_dir = _get_skills_dir()
    if not os.path.isdir(skills_dir):
        return []

    skills: list[dict[str, Any]] = []
    for entry_name in sorted(os.listdir(skills_dir)):
        skill_dir = os.path.join(skills_dir, entry_name)
        if not os.path.isdir(skill_dir):
            continue

        skill_md = os.path.join(skill_dir, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue

        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
        except (OSError, UnicodeDecodeError):
            continue

        # Parse frontmatter
        name = entry_name
        description = ""
        if content.startswith("---"):
            rest = content[3:].lstrip("\n")
            end = rest.find("\n---")
            if end >= 0:
                fm_block = rest[:end].strip()
                for line in fm_block.splitlines():
                    if ":" in line:
                        k, v = line.split(":", 1)
                        k = k.strip().lower()
                        v = v.strip().strip("'\"").strip()
                        if k == "name":
                            name = v
                        elif k == "description":
                            description = v

        skills.append({
            "slug": entry_name,
            "name": name,
            "description": description,
        })

    return skills


def get_skill(slug: str) -> dict[str, Any] | None:
    """Get a single user skill by slug with full instructions.

    Returns:
        dict with keys slug, name, description, instructions, or None if not found.
    """
    if not slug or not slug.strip():
        return None

    slug = slug.strip()
    if ".." in slug or "/" in slug or "\\" in slug:
        return None

    skills_dir = _get_skills_dir()
    skill_dir = os.path.join(skills_dir, slug)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    if not os.path.isdir(skill_dir) or not os.path.isfile(skill_md):
        return None

    try:
        with open(skill_md, "r", encoding="utf-8") as f:
            content = f.read()
    except (OSError, UnicodeDecodeError):
        return None

    name = slug
    description = ""
    body = content
    if content.startswith("---"):
        rest = content[3:].lstrip("\n")
        end = rest.find("\n---")
        if end >= 0:
            fm_block = rest[:end].strip()
            body = rest[end + 4 :].lstrip("\n")
            for line in fm_block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip().strip("'\"").strip()
                    if k == "name":
                        name = v
                    elif k == "description":
                        description = v

    return {
        "slug": slug,
        "name": name,
        "description": description,
        "instructions": body.strip(),
    }


def delete_skill(slug: str) -> bool:
    """Delete a skill by its slug.

    Args:
        slug: The slug identifier of the skill.

    Returns:
        True if the skill was deleted, False if it didn't exist.

    Raises:
        ValueError: If slug is empty or contains path traversal characters.
    """
    if not slug or not slug.strip():
        raise ValueError("Skill slug is required")

    slug = slug.strip()

    # Security: prevent path traversal
    if ".." in slug or "/" in slug or "\\" in slug:
        raise ValueError("Invalid skill slug")

    skills_dir = _get_skills_dir()
    skill_dir = os.path.join(skills_dir, slug)

    if not os.path.isdir(skill_dir):
        return False

    shutil.rmtree(skill_dir)
    return True


def update_skill(
    slug: str,
    *,
    name: str | None = None,
    description: str | None = None,
    instructions: str | None = None,
) -> dict[str, Any]:
    """Update an existing user skill by slug.

    Args:
        slug: The slug identifier of the skill.
        name: Optional new human-readable name (updates frontmatter only; slug unchanged).
        description: Optional new description.
        instructions: Optional new full instructions (replaces body).

    Returns:
        dict with keys: slug, name, description, path.

    Raises:
        ValueError: If slug is invalid or skill not found. If name/instructions are empty when provided.
    """
    if not slug or not slug.strip():
        raise ValueError("Skill slug is required")

    slug = slug.strip()

    if ".." in slug or "/" in slug or "\\" in slug:
        raise ValueError("Invalid skill slug")

    if name is not None and not name.strip():
        raise ValueError("Skill name cannot be empty")
    if instructions is not None and not instructions.strip():
        raise ValueError("Skill instructions cannot be empty")

    skills_dir = _get_skills_dir()
    skill_dir = os.path.join(skills_dir, slug)
    skill_md = os.path.join(skill_dir, "SKILL.md")

    if not os.path.isdir(skill_dir) or not os.path.isfile(skill_md):
        raise ValueError(f"Skill '{slug}' not found")

    with open(skill_md, "r", encoding="utf-8") as f:
        content = f.read()

    # Parse frontmatter and body
    current_name = slug
    current_description = ""
    body = content
    if content.startswith("---"):
        rest = content[3:].lstrip("\n")
        end = rest.find("\n---")
        if end >= 0:
            fm_block = rest[:end].strip()
            body = rest[end + 4 :].lstrip("\n")
            for line in fm_block.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    k = k.strip().lower()
                    v = v.strip().strip("'\"").strip()
                    if k == "name":
                        current_name = v
                    elif k == "description":
                        current_description = v

    new_name = name.strip() if name is not None else current_name
    new_description = (
        description.strip() if description is not None else current_description
    )
    new_body = instructions.strip() if instructions is not None else body

    frontmatter = f"---\nname: '{new_name}'\ndescription: '{new_description}'\n---\n\n"
    new_content = frontmatter + new_body

    with open(skill_md, "w", encoding="utf-8") as f:
        f.write(new_content)

    return {
        "slug": slug,
        "name": new_name,
        "description": new_description,
        "path": skill_dir,
    }
