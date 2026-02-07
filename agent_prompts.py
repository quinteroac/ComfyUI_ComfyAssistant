"""
System message assembly: system_context + user_context + skills.

System context is loaded from system_context/*.md (see user_context_loader.load_system_context).
User context (rules, SOUL, goals, skills) is loaded from user_context/ and the DB;
format_user_context() formats it for injection. Final content = system_context + user_context block.
"""


def format_user_context(user_context: dict) -> str:
    """
    Format loaded user context (rules, SOUL, goals, skills) for injection into the system message.
    Returns a string block to append; empty if no context.
    """
    if not user_context:
        return ""

    parts = []

    rules = user_context.get("rules") or []
    if rules:
        lines = ["- **Rule**: " + r.get("rule_text", "").strip() for r in rules if r.get("rule_text")]
        if lines:
            parts.append("## User rules (apply when creating or modifying workflows)\n\n" + "\n".join(lines))

    soul = (user_context.get("soul_text") or "").strip()
    goals = (user_context.get("goals_text") or "").strip()
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
        for s in skills:
            slug = s.get("slug", "?")
            text = (s.get("text") or "").strip()
            if not text:
                continue
            label = "User skill: " + slug
            if not s.get("is_full"):
                label += " (summary; apply when relevant)"
            skill_lines.append("### " + label + "\n\n" + text)
        if skill_lines:
            parts.append("## User skills (apply when relevant)\n\n" + "\n\n".join(skill_lines))

    if not parts:
        return ""

    return "\n\n---\n\n## User context (rules and skills)\n\nApply these rules and skills when creating or modifying workflows and when answering.\n\n" + "\n\n".join(parts)


def get_system_message(system_context_text: str, user_context: dict | None = None) -> dict:
    """
    Returns the complete system message for the agent.

    content = system_context + user_context (rules, SOUL, goals, skills).
    system_context_text should come from user_context_loader.load_system_context(system_context_path).
    """
    content_parts = [system_context_text]
    if user_context:
        formatted = format_user_context(user_context)
        if formatted:
            content_parts.append(formatted)
    return {
        "role": "system",
        "content": "\n\n".join(content_parts),
    }
