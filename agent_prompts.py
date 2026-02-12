"""
System message assembly: system_context + user_context + skills.

System context is loaded from system_context/*.md (see user_context_loader.load_system_context).
User context (rules, SOUL, goals, skills) is loaded from user_context/ and the DB;
format_user_context() formats it for injection. Final content = system_context + user_context block.

Context is sent in full only on the first message of a thread; subsequent messages use
get_system_message_continuation() so the same context is not re-sent every turn.
"""

# Short system message for continuation turns (context was already sent in the first message).
SYSTEM_CONTINUATION_CONTENT = (
    "You are ComfyUI Assistant. Continue the conversation. "
    "Apply the same rules, tools, and user context as in the initial system message."
)

DEFAULT_USER_CONTEXT_MAX_CHARS = 4000
DEFAULT_NARRATIVE_MAX_CHARS = 1200
DEFAULT_MAX_RULES = 12
DEFAULT_MAX_SKILLS = 8


def _truncate_text(text: str, max_chars: int) -> str:
    """Hard-truncate text with a compact suffix marker."""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    suffix = "... [truncated]"
    keep = max(0, max_chars - len(suffix))
    return text[:keep].rstrip() + suffix


def _fit_narrative(soul: str, goals: str, max_chars: int) -> tuple[str, str]:
    """Fit SOUL + goals into a shared budget while preserving both fields."""
    soul = soul.strip()
    goals = goals.strip()
    if max_chars <= 0:
        return "", ""
    if len(soul) + len(goals) <= max_chars:
        return soul, goals
    if soul and goals:
        left = max_chars // 2
        right = max_chars - left
        return _truncate_text(soul, left), _truncate_text(goals, right)
    if soul:
        return _truncate_text(soul, max_chars), ""
    return "", _truncate_text(goals, max_chars)


def _build_user_context_payload(
    rules: list[dict],
    soul: str,
    goals: str,
    rules_limit: int,
    narrative_max_chars: int,
) -> str:
    """Assemble the user context payload from rules and narrative."""
    parts = []
    if rules:
        lines = [
            "- **Rule**: " + _truncate_text(r.get("rule_text", "").strip(), 220)
            for r in rules[:rules_limit]
            if r.get("rule_text")
        ]
        omitted = len(rules) - len(lines)
        if omitted > 0:
            lines.append(f"- _{omitted} more rules omitted for brevity_")
        if lines:
            parts.append(
                "## User rules (apply when creating or modifying workflows)\n\n"
                + "\n".join(lines)
            )

    fitted_soul, fitted_goals = _fit_narrative(soul, goals, narrative_max_chars)
    if fitted_soul or fitted_goals:
        block = []
        if fitted_soul:
            block.append("**Personality / tone**: " + fitted_soul)
        if fitted_goals:
            block.append("**User goals**: " + fitted_goals)
        parts.append("## User context\n\n" + "\n\n".join(block))

    if not parts:
        return ""

    return (
        "\n\n---\n\n## User context (rules)\n\n"
        "Apply these rules when creating or modifying workflows and when answering.\n\n"
        + "\n\n".join(parts)
    )


def format_user_context(
    user_context: dict,
    max_chars: int = DEFAULT_USER_CONTEXT_MAX_CHARS,
    max_narrative_chars: int = DEFAULT_NARRATIVE_MAX_CHARS,
    max_rules: int = DEFAULT_MAX_RULES,
    metrics: dict | None = None,
) -> str:
    """
    Format loaded user context (rules, SOUL, goals) for injection into the system message.

    Uses progressive pruning instead of hard truncation: when the payload exceeds
    max_chars, rules are reduced first (whole rules, not mid-text cuts), then
    narrative budget is halved.  Hard truncation is a last-resort fallback.

    User skills are not included here; they are loaded on demand via the getUserSkill
    and listUserSkills tools.
    """
    if not user_context:
        if metrics is not None:
            metrics["user_context_chars_raw"] = 0
            metrics["user_context_chars_used"] = 0
            metrics["user_context_truncated"] = False
            metrics["user_context_rules_total"] = 0
            metrics["user_context_rules_included"] = 0
        return ""

    rules = user_context.get("rules") or []
    soul = (user_context.get("soul_text") or "").strip()
    goals = (user_context.get("goals_text") or "").strip()

    if metrics is not None:
        metrics["user_context_rules_total"] = len(rules)

    # Build payload with initial limits
    rules_limit = min(len(rules), max_rules)
    narrative_budget = max_narrative_chars
    payload = _build_user_context_payload(rules, soul, goals, rules_limit, narrative_budget)

    if metrics is not None:
        metrics["user_context_chars_raw"] = len(payload)

    if not payload:
        if metrics is not None:
            metrics["user_context_chars_used"] = 0
            metrics["user_context_truncated"] = False
            metrics["user_context_rules_included"] = 0
        return ""

    # Progressive pruning: reduce rules count, then narrative budget
    truncated = False
    if len(payload) > max_chars and rules_limit > 0:
        # Phase 1: halve rules count iteratively
        while rules_limit > 1 and len(payload) > max_chars:
            rules_limit = max(1, rules_limit // 2)
            payload = _build_user_context_payload(rules, soul, goals, rules_limit, narrative_budget)
            truncated = True

    if len(payload) > max_chars and narrative_budget > 200:
        # Phase 2: halve narrative budget
        narrative_budget = narrative_budget // 2
        payload = _build_user_context_payload(rules, soul, goals, rules_limit, narrative_budget)
        truncated = True

    if len(payload) > max_chars:
        # Phase 3: last resort — hard truncation
        payload = _truncate_text(payload, max_chars)
        truncated = True

    if metrics is not None:
        metrics["user_context_rules_included"] = rules_limit
        metrics["user_context_chars_used"] = len(payload)
        metrics["user_context_truncated"] = truncated

    return payload


def _format_user_skills_index(user_skills: list[dict]) -> str:
    """Build a compact index of user skills (slug + description, one line each)."""
    if not user_skills:
        return ""
    lines = []
    for skill in user_skills:
        slug = skill.get("slug", "")
        name = skill.get("name", slug)
        desc = skill.get("description", "")
        if desc:
            lines.append(f"- **{name}** (`{slug}`): {desc}")
        else:
            lines.append(f"- **{name}** (`{slug}`)")
    return "\n".join(lines)


def get_system_message(
    system_context_text: str,
    user_context: dict | None = None,
    environment_summary: str = "",
    user_context_max_chars: int = DEFAULT_USER_CONTEXT_MAX_CHARS,
    user_skills: list[dict] | None = None,
    metrics: dict | None = None,
) -> dict:
    """
    Returns the complete system message for the agent.

    content = system_context + environment_summary + user_context (rules, SOUL, goals, skills).
    system_context_text should come from user_context_loader.load_system_context(system_context_path).
    environment_summary is a brief text from environment_scanner.get_environment_summary().
    user_skills is an optional list of {slug, name, description} from skill_manager.list_skills().
    """
    content_parts = [system_context_text]

    # User skills: show index if available, instruct to load full content on demand
    skills_index = _format_user_skills_index(user_skills or [])
    if skills_index:
        content_parts.append(
            "## User skills\n\n"
            "The following user skills (saved preferences) are available. "
            "Call getUserSkill(slug) to load a skill's full instructions "
            "when the user refers to it or when you need to apply a remembered preference.\n\n"
            + skills_index
        )
    else:
        content_parts.append(
            "## User skills\n\n"
            "No user skills saved yet. Use createSkill to save a new skill "
            "when the user asks to remember a preference or instruction."
        )

    # Model skills: headers are visible in the system context above
    content_parts.append(
        "## Model-specific system skills\n\n"
        "Model skill headers are visible above (e.g. Flux, SDXL, Lumina2, Wan). "
        "These headers show which models have dedicated workflow instructions.\n\n"
        "**When the user asks about a model or a workflow for a model**: call "
        "getSystemSkill(slug) to load that skill's full instructions before answering "
        "or building the workflow (e.g. Flux → 09_model_flux, SDXL → 13_model_sdxl). "
        "Apply the loaded skill content when giving advice or creating workflows for that model."
    )
    if environment_summary:
        content_parts.append(
            "## Installed environment\n\n" + environment_summary
        )
    if metrics is not None:
        metrics["environment_summary_chars"] = len(environment_summary)
        metrics["user_skills_count"] = len(user_skills) if user_skills else 0
    if user_context:
        formatted = format_user_context(
            user_context,
            max_chars=user_context_max_chars,
            metrics=metrics,
        )
        if formatted:
            content_parts.append(formatted)
    return {
        "role": "system",
        "content": "\n\n".join(content_parts),
    }


def get_system_message_continuation() -> dict:
    """
    Returns a minimal system message for continuation turns.

    Use this when the conversation already has at least one assistant message:
    the full context was sent in the first turn, so we only send a short reminder
    to avoid re-sending the same long context on every request.
    """
    return {
        "role": "system",
        "content": SYSTEM_CONTINUATION_CONTENT,
    }
