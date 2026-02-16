"""Slash command handling for skills and provider management."""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
from typing import Any

import provider_manager
import provider_store
import skill_manager
import user_context_store

logger = logging.getLogger("ComfyUI_ComfyAssistant.slash_commands")

_PERSONA_SLUG_RE = re.compile(r"^[a-z0-9](?:[a-z0-9_-]{0,61}[a-z0-9])?$")
_PERSONA_FLOW_RE = re.compile(r"<!--\s*local:persona-create\s*(\{.*?\})\s*-->", re.DOTALL)

# #region agent log
def _debug_log(location: str, message: str, data: dict | None = None, hypothesis_id: str = "A") -> None:
    import time
    try:
        payload = {"id": f"log_{int(time.time()*1000)}", "timestamp": int(time.time()*1000), "location": location, "message": message, "hypothesisId": hypothesis_id}
        if data is not None:
            payload["data"] = data
        with open(os.path.join(os.path.dirname(__file__), ".cursor", "debug.log"), "a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion


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


def _looks_like_persona_create_request(text: str) -> bool:
    normalized = (text or "").strip().lower()
    if normalized.startswith("/persona create"):
        return True
    return normalized in {
        "create persona",
        "create a persona",
        "i want to create a persona",
        "i want to create persona",
        "new persona",
    }


def _extract_last_persona_flow_state(openai_messages: list[dict]) -> dict[str, str] | None:
    for i in range(len(openai_messages) - 1, -1, -1):
        message = openai_messages[i]
        if message.get("role") != "assistant":
            continue
        content = _openai_message_content_to_str(message)
        match = _PERSONA_FLOW_RE.search(content)
        if not match:
            continue
        try:
            parsed = json.loads(match.group(1))
        except json.JSONDecodeError:
            return None
        if not isinstance(parsed, dict):
            return None
        result = {
            "state": str(parsed.get("state") or "").strip(),
            "name": str(parsed.get("name") or "").strip(),
            "slug": str(parsed.get("slug") or "").strip(),
            "description": str(parsed.get("description") or "").strip(),
        }
        # #region agent log
        _debug_log("slash_commands._extract_last_persona_flow_state", "extracted flow state", {"message_index": i, "state": result["state"], "num_messages": len(openai_messages)})
        # #endregion
        return result
    return None


def _with_persona_flow_state(text: str, state: dict[str, str]) -> str:
    return f"{text}\n\n<!-- local:persona-create {json.dumps(state, ensure_ascii=True)} -->"


def _slugify_persona_name(name: str) -> str:
    slug = (name or "").strip().lower()
    slug = slug.replace(" ", "-").replace("_", "-")
    slug = re.sub(r"-+", "-", slug)
    slug = re.sub(r"[^a-z0-9-]", "", slug)
    return slug.strip("-")


def _is_valid_persona_slug(slug: str) -> bool:
    return bool(_PERSONA_SLUG_RE.fullmatch((slug or "").strip()))


def _find_provider_by_user_input(user_input: str) -> dict | None:
    needle = (user_input or "").strip().lower()
    if not needle:
        return None
    for provider in provider_store.get_all_providers():
        name = str(provider.get("name") or "").strip().lower()
        display_name = str(provider.get("display_name") or "").strip().lower()
        if needle == name or needle == display_name:
            return provider
    return None


def _write_persona_soul(
    *,
    name: str,
    slug: str,
    description: str,
    provider_name: str,
) -> None:
    root = user_context_store.ensure_user_context_dirs()
    persona_dir = os.path.join(root, "personas", slug)
    soul_path = os.path.join(persona_dir, "SOUL.md")
    if os.path.exists(persona_dir):
        raise ValueError(f'Persona "{slug}" already exists.')

    os.makedirs(persona_dir, exist_ok=False)
    frontmatter_name = " ".join(name.splitlines()).strip()
    frontmatter_description = " ".join(description.splitlines()).strip()
    body = description.strip()
    if not body:
        raise ValueError("Persona description cannot be empty.")

    content = (
        "---\n"
        f"Name: {frontmatter_name}\n"
        f"Description: {frontmatter_description}\n"
        f"Provider: {provider_name}\n"
        "---\n\n"
        f"{body}\n"
    )
    with open(soul_path, "w", encoding="utf-8") as soul_file:
        soul_file.write(content)


def _parse_frontmatter(content: str) -> tuple[dict[str, str], str]:
    """Parse simple YAML frontmatter + markdown body from SOUL.md."""
    frontmatter: dict[str, str] = {}
    body = content.strip()
    if not body.startswith("---"):
        return (frontmatter, body)

    rest = body[3:].lstrip("\n")
    end = rest.find("\n---")
    if end < 0:
        return ({}, "")

    frontmatter_block = rest[:end].strip()
    body = rest[end + 4:].strip()
    for line in frontmatter_block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip().lower()] = value.strip().strip("'\"").strip()
    return (frontmatter, body)


def _load_persona_by_slug(slug: str) -> dict[str, str] | None:
    """Load persona metadata from user_context/personas/<slug>/SOUL.md."""
    if not _is_valid_persona_slug(slug):
        return None
    root = user_context_store.ensure_user_context_dirs()
    soul_path = os.path.join(root, "personas", slug, "SOUL.md")
    if not os.path.isfile(soul_path):
        return None
    try:
        with open(soul_path, "r", encoding="utf-8") as soul_file:
            raw = soul_file.read()
    except OSError:
        return None
    frontmatter, body = _parse_frontmatter(raw)
    name = (frontmatter.get("name") or "").strip()
    description = (frontmatter.get("description") or "").strip()
    provider = (frontmatter.get("provider") or "").strip()
    if not name or not description or not provider or not body.strip():
        return None
    return {
        "slug": slug,
        "name": name,
        "description": description,
        "provider": provider,
    }


def _list_personas() -> list[dict[str, str]]:
    """List valid persona records from user_context/personas/."""
    personas: list[dict[str, str]] = []
    root = user_context_store.ensure_user_context_dirs()
    personas_dir = os.path.join(root, "personas")
    if not os.path.isdir(personas_dir):
        return personas
    for name in sorted(os.listdir(personas_dir)):
        slug = (name or "").strip().lower()
        persona = _load_persona_by_slug(slug)
        if persona:
            personas.append(persona)
    return personas


def _format_persona_line(persona: dict[str, str], active_slug: str) -> str:
    marker = "✓" if active_slug and persona["slug"] == active_slug else " "
    description = persona.get("description", "").strip()
    if len(description) > 90:
        description = f"{description[:87].rstrip()}..."
    return (
        f"{marker} **{persona['name']}** (`{persona['slug']}`) · "
        f"provider `{persona['provider']}` · {description}"
    )


def _handle_persona_list() -> dict:
    """Handle `/persona` or `/persona list` commands."""
    personas = _list_personas()
    if not personas:
        return {"text": "No personas are available yet. Run `/persona create` first."}

    active_slug = str(user_context_store.get_preferences().get("active_persona") or "").strip().lower()
    lines = [
        "**Available Personas**",
        "",
    ]
    for persona in personas:
        lines.append(_format_persona_line(persona, active_slug))
    lines.append("")
    lines.append("Use `/persona <name-or-slug>` to switch personas.")
    lines.append("Use `/persona del <name-or-slug>` to delete one.")
    return {"text": "\n".join(lines)}


def _resolve_persona_by_name_or_slug(token: str) -> dict[str, str] | None:
    """Resolve persona by exact slug or case-insensitive Name frontmatter."""
    needle = (token or "").strip()
    if not needle:
        return None
    slug_candidate = _slugify_persona_name(needle)
    if _is_valid_persona_slug(slug_candidate):
        exact = _load_persona_by_slug(slug_candidate)
        if exact:
            return exact
    needle_lower = needle.lower()
    for persona in _list_personas():
        if needle_lower == persona["name"].strip().lower():
            return persona
    return None


def _delete_persona_folder(slug: str) -> None:
    """Delete user_context/personas/<slug> recursively."""
    if not _is_valid_persona_slug(slug):
        raise ValueError("Invalid persona slug.")
    root = user_context_store.ensure_user_context_dirs()
    persona_dir = os.path.join(root, "personas", slug)
    if not os.path.isdir(persona_dir):
        raise FileNotFoundError(f'Persona "{slug}" does not exist.')
    shutil.rmtree(persona_dir)


def _handle_persona_switch(command_text: str) -> dict:
    """Handle `/persona <name-or-slug>` switch command."""
    parts = command_text.strip().split(maxsplit=1)
    if len(parts) < 2 or not parts[1].strip():
        return _handle_persona_list()

    token = parts[1].strip()
    lowered_token = token.lower()
    if lowered_token == "create":
        return {"text": "Run `/persona create` and answer the next prompts to create a persona."}
    if lowered_token == "list":
        return _handle_persona_list()

    persona = _resolve_persona_by_name_or_slug(token)
    if not persona:
        available = _list_personas()
        if not available:
            return {"text": "Persona not found and no personas are available yet. Run `/persona create` first."}
        options = ", ".join(
            f"`{record['slug']}`" for record in available
        )
        return {"text": f"Persona `{token}` not found. Available personas: {options}"}

    provider_name = persona["provider"]
    provider = provider_store.get_provider_by_name(provider_name)
    if not provider:
        return {"text": f'Persona `{persona["slug"]}` references provider `{provider_name}`, but that provider is not configured.'}

    if not provider_store.set_active_provider(provider_name):
        return {"text": f"Could not activate provider `{provider_name}` for persona `{persona['slug']}`."}

    user_context_store.add_or_update_preference("active_persona", persona["slug"])
    provider_manager.reload_provider()
    return {
        "text": (
            f'✓ Active persona set to **{persona["name"]}** (`{persona["slug"]}`).\n\n'
            f'Provider switched to `{provider_name}`. '
            "New messages will use this persona and provider."
        )
    }


def _handle_persona_delete(command_text: str) -> dict:
    """Handle `/persona del <name-or-slug>` delete command."""
    parts = command_text.strip().split(maxsplit=2)
    if len(parts) < 3 or not parts[2].strip():
        return {"text": "Usage: `/persona del <name>`"}

    token = parts[2].strip()
    persona = _resolve_persona_by_name_or_slug(token)
    if not persona:
        available = _list_personas()
        if not available:
            return {"text": "Persona not found and no personas are available yet."}
        options = ", ".join(f"`{record['slug']}`" for record in available)
        return {"text": f"Persona `{token}` not found. Available personas: {options}"}

    try:
        _delete_persona_folder(persona["slug"])
    except FileNotFoundError:
        return {"text": f'Persona `{persona["slug"]}` does not exist.'}
    except OSError as exc:
        return {"text": f'Could not delete persona `{persona["slug"]}`: {exc}'}

    active_slug = str(user_context_store.get_preferences().get("active_persona") or "").strip().lower()
    if active_slug == persona["slug"]:
        user_context_store.add_or_update_preference("active_persona", "")
        return {
            "text": (
                f'Persona **{persona["name"]}** (`{persona["slug"]}`) was deleted.\n\n'
                "It was the active persona, so the assistant fell back to the default personality. "
                "Use `/persona <name>` to select another persona."
            )
        }

    return {
        "text": f'Persona **{persona["name"]}** (`{persona["slug"]}`) was deleted.'
    }


def handle_persona_command(
    *,
    command_text: str,
    openai_messages: list[dict],
) -> dict | None:
    """
    Handle local persona commands:
    - `/persona create` conversational flow
    - `/persona <name>` switch flow
    - plain text persona-create triggers ("create persona", etc.)

    Returns {"text": "..."} for local response, or None when not applicable.
    """
    user_text = (command_text or "").strip()
    lower_user_text = user_text.lower()
    flow_state = _extract_last_persona_flow_state(openai_messages)
    # #region agent log
    _debug_log("slash_commands.handle_persona_command", "entry", {"flow_state": flow_state, "state_name": flow_state.get("state", "") if flow_state else None, "user_text_preview": user_text[:80] if user_text else ""})
    # #endregion

    # Flow completed (persona created); next message is normal chat.
    if flow_state and flow_state.get("state") == "created":
        return None

    is_persona_command = lower_user_text.startswith("/persona")
    wants_create_flow = _looks_like_persona_create_request(user_text)
    if flow_state is None and not (wants_create_flow or is_persona_command):
        return None

    # Single-turn persona switching/deletion: handle explicit commands even if create flow was in progress.
    if is_persona_command and not lower_user_text.startswith("/persona create"):
        if (
            lower_user_text.startswith("/persona del ")
            or lower_user_text == "/persona del"
            or lower_user_text.startswith("/persona delete ")
            or lower_user_text == "/persona delete"
        ):
            return _handle_persona_delete(user_text)
        return _handle_persona_switch(user_text)

    if lower_user_text in {"/cancel", "cancel"}:
        return {"text": "Persona creation cancelled."}

    if flow_state is None:
        return {
            "text": _with_persona_flow_state(
                "What will be the name of the persona?",
                {"state": "await_name"},
            )
        }

    state_name = flow_state.get("state", "")
    if state_name == "await_name":
        persona_name = user_text.strip()
        if not persona_name:
            return {
                "text": _with_persona_flow_state(
                    "What will be the name of the persona?",
                    {"state": "await_name"},
                )
            }
        slug = _slugify_persona_name(persona_name)
        if not _is_valid_persona_slug(slug):
            return {
                "text": _with_persona_flow_state(
                    "That name is not valid. Use letters, numbers, or hyphens only.",
                    {"state": "await_name"},
                )
            }
        return {
            "text": _with_persona_flow_state(
                "Can you describe the personality? (behavior, background, specialty...)",
                {"state": "await_description", "name": persona_name, "slug": slug},
            )
        }

    if state_name == "await_description":
        description = user_text.strip()
        if not description:
            return {
                "text": _with_persona_flow_state(
                    "Can you describe the personality? (behavior, background, specialty...)",
                    {
                        "state": "await_description",
                        "name": flow_state.get("name", ""),
                        "slug": flow_state.get("slug", ""),
                    },
                )
            }
        providers = provider_store.get_all_providers()
        if not providers:
            return {"text": "No configured providers found. Configure one in `/provider-settings`, then run `/persona create` again."}
        lines = [
            "Which provider will represent the persona?",
            "",
            "**Configured Providers**",
            "",
        ]
        active = provider_store.get_active_provider()
        active_name = active.get("name") if active else None
        for provider in providers:
            lines.append(_format_provider_line(provider, active_name))
        lines.append("")
        lines.append("Reply with the provider `name` (value inside backticks).")
        return {
            "text": _with_persona_flow_state(
                "\n".join(lines),
                {
                    "state": "await_provider",
                    "name": flow_state.get("name", ""),
                    "slug": flow_state.get("slug", ""),
                    "description": description,
                },
            )
        }

    if state_name == "await_provider":
        provider = _find_provider_by_user_input(user_text)
        if not provider:
            providers = provider_store.get_all_providers()
            names = ", ".join(
                f"`{p.get('name')}`" for p in providers if p.get("name")
            )
            # #region agent log
            _debug_log("slash_commands.handle_persona_command", "Provider not found branch", {"user_text_preview": user_text[:80], "flow_state_state": flow_state.get("state")})
            # #endregion
            return {
                "text": _with_persona_flow_state(
                    f"Provider not found. Choose one of: {names}",
                    flow_state,
                )
            }
        persona_name = flow_state.get("name", "").strip()
        slug = flow_state.get("slug", "").strip()
        description = flow_state.get("description", "").strip()
        if not persona_name or not slug or not description:
            return {"text": "Persona creation state is incomplete. Run `/persona create` to start again."}
        try:
            _write_persona_soul(
                name=persona_name,
                slug=slug,
                description=description,
                provider_name=str(provider.get("name") or ""),
            )
        except ValueError as exc:
            return {"text": str(exc)}
        except OSError as exc:
            return {"text": f"Could not create persona files: {exc}"}
        provider_name = str(provider.get("name") or "")
        provider_store.set_active_provider(provider_name)
        user_context_store.add_or_update_preference("active_persona", slug)
        provider_manager.reload_provider()
        # #region agent log
        _debug_log("slash_commands.handle_persona_command", "Persona created success (state=created in response)", {"slug": slug, "provider_name": provider_name})
        # #endregion
        success_text = (
            f'Persona **{persona_name}** created at '
            f'`user_context/personas/{slug}/SOUL.md` with provider '
            f'`{provider_name}`. Active persona and provider set; new messages will use them.'
        )
        return {
            "text": _with_persona_flow_state(
                success_text,
                {"state": "created", "slug": slug},
            )
        }

    return {"text": "Persona creation state is invalid. Run `/persona create` to start again."}
