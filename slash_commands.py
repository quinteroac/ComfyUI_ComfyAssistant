"""Slash command handling for skills and provider management."""

from __future__ import annotations

import logging
import re
from typing import Any

import provider_manager
import provider_store
import skill_manager

logger = logging.getLogger("ComfyUI_ComfyAssistant.slash_commands")


def _openai_message_content_to_str(msg: dict[str, Any]) -> str:
    """Extract plain text content from an OpenAI-format message."""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            str(p.get("text", "")) for p in content if isinstance(p, dict)
        )
    return ""


def _set_openai_message_content(msg: dict[str, Any], text: str) -> None:
    """Set an OpenAI-format message content to a plain string."""
    msg["content"] = text


def _resolve_skill_by_name_or_slug(arg: str) -> dict | None:
    """Find a user skill by slug or name. Returns skill dict (slug, name, description, instructions) or None."""
    if not arg or not arg.strip():
        return None
    arg = arg.strip()
    slug_candidate = arg.lower().replace(" ", "-").replace("_", "-")
    slug_candidate = re.sub(r"-+", "-", slug_candidate).strip("-")
    all_skills = skill_manager.list_skills()
    for s in all_skills:
        slug = s.get("slug", "")
        name = (s.get("name") or "").strip()
        if slug and (slug == arg or slug == slug_candidate):
            return skill_manager.get_skill(slug)
        if name and arg.lower() in name.lower():
            return skill_manager.get_skill(slug)
    if slug_candidate:
        return skill_manager.get_skill(slug_candidate)
    return None


def _inject_skill_if_slash_skill(openai_messages: list[dict]) -> None:
    """If the last user message is /skill <name>, resolve the skill and inject it for this turn."""
    if not openai_messages:
        return
    last_user_idx = None
    for i in range(len(openai_messages) - 1, -1, -1):
        if openai_messages[i].get("role") == "user":
            last_user_idx = i
            break
    if last_user_idx is None:
        return
    content = _openai_message_content_to_str(openai_messages[last_user_idx])
    raw = content.strip()
    if not raw.lower().startswith("/skill"):
        return
    arg = raw[6:].strip() if len(raw) > 6 else ""  # after "/skill"
    if not arg:
        _set_openai_message_content(
            openai_messages[last_user_idx],
            "The user typed /skill but did not specify a skill name. Suggest they use listUserSkills to see available skills.",
        )
        return
    skill = _resolve_skill_by_name_or_slug(arg)
    if not skill:
        _set_openai_message_content(
            openai_messages[last_user_idx],
            f'The user tried to activate a skill "{arg}" but it was not found. Suggest they use listUserSkills to see available skills.',
        )
        return
    instructions = (skill.get("instructions") or "").strip()
    name = (skill.get("name") or skill.get("slug", "?")).strip()
    block = (
        "\n\n## Active skill (this turn)\n\n"
        f"User activated: **{name}**\n\n{instructions}"
    )
    for m in openai_messages:
        if m.get("role") == "system":
            prev = m.get("content") or ""
            m["content"] = prev + block
            break
    _set_openai_message_content(
        openai_messages[last_user_idx],
        f'The user activated the skill "{name}". Apply the instructions above.',
    )


def _format_provider_line(provider: dict, active_name: str | None) -> str:
    marker = "✓" if active_name and provider.get("name") == active_name else " "
    display_name = provider.get("display_name") or provider.get("name") or "Unnamed"
    name = provider.get("name") or "unknown"
    provider_type = provider.get("provider_type") or "unknown"
    return f"{marker} **{display_name}** (`{name}`) · {provider_type}"


def _handle_provider_command(command_text: str) -> dict:
    """Handle /provider commands and return local text response."""
    parts = command_text.strip().split()
    if len(parts) < 2:
        return {"text": "Usage: /provider <set|list> [name]"}

    subcommand = parts[1].lower()
    if subcommand == "list":
        providers = provider_store.get_all_providers()
        active = provider_store.get_active_provider()
        active_name = active.get("name") if active else None
        if not providers:
            return {"text": "No providers configured yet. Run `/provider-settings`."}
        lines = ["**Configured Providers**", ""]
        for provider in providers:
            lines.append(_format_provider_line(provider, active_name))
        return {"text": "\n".join(lines)}

    if subcommand == "set":
        if len(parts) < 3:
            return {"text": "Usage: /provider set <name>"}
        name = parts[2].strip()
        if not name:
            return {"text": "Usage: /provider set <name>"}
        success = provider_store.set_active_provider(name)
        if not success:
            return {"text": f"Provider `{name}` not found."}
        provider_manager.reload_provider()
        return {
            "text": (
                f"✓ Active provider set to **{name}**.\n\n"
                "New messages will use this provider."
            )
        }

    return {"text": f"Unknown subcommand: `{subcommand}`. Use `/provider list` or `/provider set <name>`."}
