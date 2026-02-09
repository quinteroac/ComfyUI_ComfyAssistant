"""
Documentation resolver for ComfyUI Assistant.

Resolves documentation for topics by searching system_context/ skills,
NODE_CLASS_MAPPINGS input/output info, and custom_nodes' .agents/ and README.md.
"""

import json
import logging
import os
from typing import Any

logger = logging.getLogger("ComfyUI_ComfyAssistant.doc_resolver")

# Maximum characters to return from third-party content (security boundary)
MAX_CONTENT_CHARS = 2000


def _strip_html(text: str) -> str:
    """Remove HTML tags from text (basic sanitization)."""
    import re
    return re.sub(r'<[^>]+>', '', text)


def _truncate(text: str, max_chars: int = MAX_CONTENT_CHARS) -> str:
    """Truncate text to max_chars, adding ellipsis if truncated."""
    text = text.strip()
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n... (truncated)"


def _read_file_safe(path: str, max_chars: int = MAX_CONTENT_CHARS) -> str:
    """Read a file safely with size limit and HTML stripping."""
    if not os.path.isfile(path):
        return ""
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read(max_chars + 1000)  # Read a bit extra for truncation
        content = _strip_html(content)
        return _truncate(content, max_chars)
    except (OSError, UnicodeDecodeError):
        return ""


def resolve_node_type_info(node_type: str) -> dict[str, Any] | None:
    """Get detailed info for a specific node type from NODE_CLASS_MAPPINGS.

    Returns dict with name, category, inputs, outputs, description,
    or None if not found.
    """
    try:
        import nodes
    except ImportError:
        return None

    node_map = getattr(nodes, "NODE_CLASS_MAPPINGS", {})
    cls = node_map.get(node_type)
    if cls is None:
        return None

    info: dict[str, Any] = {
        "name": node_type,
        "category": getattr(cls, "CATEGORY", "uncategorized"),
        "description": getattr(cls, "DESCRIPTION", ""),
    }

    # Extract input types
    inputs: dict[str, Any] = {}
    try:
        input_types = cls.INPUT_TYPES() if callable(getattr(cls, "INPUT_TYPES", None)) else {}
        for section in ("required", "optional", "hidden"):
            section_data = input_types.get(section, {})
            for input_name, input_spec in section_data.items():
                if isinstance(input_spec, (list, tuple)) and len(input_spec) > 0:
                    type_info = input_spec[0]
                    if isinstance(type_info, list):
                        inputs[input_name] = {
                            "type": "COMBO",
                            "options": type_info[:20],
                            "section": section,
                        }
                    elif isinstance(type_info, str):
                        config = input_spec[1] if len(input_spec) > 1 and isinstance(input_spec[1], dict) else {}
                        entry: dict[str, Any] = {"type": type_info, "section": section}
                        for k in ("default", "min", "max", "step", "multiline"):
                            if k in config:
                                entry[k] = config[k]
                        inputs[input_name] = entry
                    else:
                        inputs[input_name] = {"type": str(type_info), "section": section}
                else:
                    inputs[input_name] = {"type": str(input_spec), "section": section}
    except Exception:
        pass

    info["inputs"] = inputs

    # Output types
    output_types = getattr(cls, "RETURN_TYPES", ())
    output_names = getattr(cls, "RETURN_NAMES", ())
    outputs = []
    for i, otype in enumerate(output_types):
        oname = output_names[i] if i < len(output_names) else str(otype)
        outputs.append({"type": str(otype), "name": str(oname)})
    info["outputs"] = outputs

    # Function name
    info["function"] = getattr(cls, "FUNCTION", "")

    # Source module
    module = getattr(cls, "__module__", "")
    parts = module.split(".")
    if len(parts) >= 2 and parts[0] == "custom_nodes":
        info["package"] = parts[1]
    else:
        info["package"] = "built-in"

    return info


def _search_system_context(topic: str, system_context_dir: str) -> str:
    """Search system_context/ skills for topic mentions."""
    if not os.path.isdir(system_context_dir):
        return ""

    topic_lower = topic.lower()
    results: list[str] = []

    skills_dir = os.path.join(system_context_dir, "skills")
    if os.path.isdir(skills_dir):
        for name in sorted(os.listdir(skills_dir)):
            skill_dir = os.path.join(skills_dir, name)
            if not os.path.isdir(skill_dir):
                continue
            skill_md = os.path.join(skill_dir, "SKILL.md")
            content = _read_file_safe(skill_md, 3000)
            if content and topic_lower in content.lower():
                results.append(f"## From system skill: {name}\n\n{_truncate(content, 800)}")

    return "\n\n".join(results) if results else ""


def _search_custom_node_docs(topic: str, custom_nodes_dir: str | None = None) -> str:
    """Search custom nodes' .agents/ and README.md for topic documentation."""
    if custom_nodes_dir is None:
        custom_nodes_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if not os.path.isdir(custom_nodes_dir):
        return ""

    topic_lower = topic.lower()
    results: list[str] = []
    chars_used = 0

    for entry_name in sorted(os.listdir(custom_nodes_dir)):
        if chars_used >= MAX_CONTENT_CHARS:
            break

        entry_path = os.path.join(custom_nodes_dir, entry_name)
        if not os.path.isdir(entry_path):
            continue
        if entry_name.startswith(".") or entry_name == "__pycache__":
            continue

        # Check if package name matches topic
        if topic_lower not in entry_name.lower():
            continue

        # Try .agents/ directory first
        agents_dir = os.path.join(entry_path, ".agents")
        if os.path.isdir(agents_dir):
            for fname in os.listdir(agents_dir):
                if fname.endswith(".md"):
                    content = _read_file_safe(os.path.join(agents_dir, fname), 800)
                    if content:
                        remaining = MAX_CONTENT_CHARS - chars_used
                        excerpt = _truncate(content, min(800, remaining))
                        results.append(f"## From {entry_name}/.agents/{fname}\n\n{excerpt}")
                        chars_used += len(excerpt)
                        if chars_used >= MAX_CONTENT_CHARS:
                            break

        # Try README.md
        if chars_used < MAX_CONTENT_CHARS:
            readme_path = os.path.join(entry_path, "README.md")
            content = _read_file_safe(readme_path, MAX_CONTENT_CHARS - chars_used)
            if content:
                remaining = MAX_CONTENT_CHARS - chars_used
                excerpt = _truncate(content, min(1000, remaining))
                results.append(f"## From {entry_name}/README.md\n\n{excerpt}")
                chars_used += len(excerpt)

    return "\n\n".join(results) if results else ""


def resolve_documentation(
    topic: str,
    source: str = "any",
    system_context_dir: str | None = None,
    custom_nodes_dir: str | None = None,
) -> dict[str, Any]:
    """Search for documentation about a topic.

    Args:
        topic: What to search for (node type name, concept, package name).
        source: 'installed' (custom nodes only), 'builtin' (system context only), or 'any'.
        system_context_dir: Path to system_context/ directory.
        custom_nodes_dir: Path to custom_nodes/ directory.

    Returns:
        dict with keys: topic, source, content (string), node_info (if applicable).
    """
    result: dict[str, Any] = {
        "topic": topic,
        "source": source,
        "content": "",
        "node_info": None,
    }

    parts: list[str] = []

    # Always try to get node type info (it's fast and useful)
    node_info = resolve_node_type_info(topic)
    if node_info:
        result["node_info"] = node_info
        # Format node info as readable text
        info_text = f"**{node_info['name']}** (category: {node_info['category']}, package: {node_info['package']})\n\n"
        if node_info.get("description"):
            info_text += f"{node_info['description']}\n\n"
        if node_info.get("inputs"):
            info_text += "**Inputs:**\n"
            for name, spec in node_info["inputs"].items():
                section = spec.get("section", "")
                type_str = spec.get("type", "unknown")
                detail = f"  - `{name}` ({type_str}, {section})"
                if "default" in spec:
                    detail += f" default={spec['default']}"
                if "options" in spec:
                    opts = spec["options"][:5]
                    detail += f" options={opts}"
                info_text += detail + "\n"
            info_text += "\n"
        if node_info.get("outputs"):
            info_text += "**Outputs:**\n"
            for out in node_info["outputs"]:
                info_text += f"  - `{out['name']}` ({out['type']})\n"
        parts.append(info_text)

    # Search system context (builtin skills/docs)
    if source in ("builtin", "any") and system_context_dir:
        sys_docs = _search_system_context(topic, system_context_dir)
        if sys_docs:
            parts.append(sys_docs)

    # Search custom node documentation
    if source in ("installed", "any"):
        custom_docs = _search_custom_node_docs(topic, custom_nodes_dir)
        if custom_docs:
            parts.append(custom_docs)

    if parts:
        result["content"] = _truncate("\n\n".join(parts), MAX_CONTENT_CHARS)
    else:
        result["content"] = f"No documentation found for '{topic}'."

    return result
