"""
System message assembly: system_context + user_context + skills.

System context is loaded from system_context/*.md (see user_context_loader.load_system_context).
User context (rules, SOUL, goals, skills) is loaded from user_context/ and the DB;
format_user_context() formats it for injection. Final content = system_context + user_context block.
"""

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


def format_user_context(
    user_context: dict,
    max_chars: int = DEFAULT_USER_CONTEXT_MAX_CHARS,
    max_narrative_chars: int = DEFAULT_NARRATIVE_MAX_CHARS,
    max_rules: int = DEFAULT_MAX_RULES,
    max_skills: int = DEFAULT_MAX_SKILLS,
) -> str:
    """
    Format loaded user context (rules, SOUL, goals, skills) for injection into the system message.
    Returns a string block to append; empty if no context.
    """
    if not user_context:
        return ""

    parts = []

    rules = user_context.get("rules") or []
    if rules:
        lines = [
            "- **Rule**: " + _truncate_text(r.get("rule_text", "").strip(), 220)
            for r in rules[:max_rules]
            if r.get("rule_text")
        ]
        omitted = len(rules) - len(lines)
        if omitted > 0:
            lines.append(f"- _{omitted} more rules omitted for brevity_")
        if lines:
            parts.append("## User rules (apply when creating or modifying workflows)\n\n" + "\n".join(lines))

    soul = (user_context.get("soul_text") or "").strip()
    goals = (user_context.get("goals_text") or "").strip()
    soul, goals = _fit_narrative(soul, goals, max_narrative_chars)
    if soul or goals:
        block = []
        if soul:
            block.append("**Personality / tone**: " + soul)
        if goals:
            block.append("**User goals**: " + goals)
        parts.append("## User context\n\n" + "\n\n".join(block))

    skills = user_context.get("skills") or []
    if skills:
        skill_lines = []
        for s in skills[:max_skills]:
            slug = s.get("slug", "?")
            text = _truncate_text((s.get("text") or "").strip(), 360)
            if not text:
                continue
            label = "User skill: " + slug
            if not s.get("is_full"):
                label += " (summary; apply when relevant)"
            skill_lines.append("### " + label + "\n\n" + text)
        omitted = len(skills) - len(skill_lines)
        if omitted > 0:
            skill_lines.append(f"_... {omitted} more skills omitted for brevity_")
        if skill_lines:
            parts.append("## User skills (apply when relevant)\n\n" + "\n\n".join(skill_lines))

    if not parts:
        return ""

    payload = (
        "\n\n---\n\n## User context (rules and skills)\n\n"
        "Apply these rules and skills when creating or modifying workflows and "
        "when answering.\n\n" + "\n\n".join(parts)
    )
    return _truncate_text(payload, max_chars)


def get_system_message(
    system_context_text: str,
    user_context: dict | None = None,
    environment_summary: str = "",
    user_context_max_chars: int = DEFAULT_USER_CONTEXT_MAX_CHARS,
) -> dict:
    """
    Returns the complete system message for the agent.

    content = system_context + environment_summary + user_context (rules, SOUL, goals, skills).
    system_context_text should come from user_context_loader.load_system_context(system_context_path).
    environment_summary is a brief text from environment_scanner.get_environment_summary().
    """
    content_parts = [system_context_text]
    if environment_summary:
        content_parts.append(
            "## Installed environment\n\n" + environment_summary
        )
    if user_context:
        formatted = format_user_context(
            user_context,
            max_chars=user_context_max_chars
        )
        if formatted:
            content_parts.append(formatted)
    return {
        "role": "system",
        "content": "\n\n".join(content_parts),
    }
