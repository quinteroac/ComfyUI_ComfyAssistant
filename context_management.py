"""Context management: truncation, history trimming, token estimation, and message compaction."""

from __future__ import annotations

import json
import logging

logger = logging.getLogger("ComfyUI_ComfyAssistant.context_management")

LLM_SYSTEM_CONTEXT_MAX_CHARS = 12000
LLM_USER_CONTEXT_MAX_CHARS = 2500
LLM_HISTORY_MAX_MESSAGES = 24
# Keep full tool result content only for the last N "rounds" (each round = one assistant tool_calls + its tool replies). Older rounds get a short placeholder to avoid context growth.
LLM_TOOL_RESULT_KEEP_LAST_ROUNDS = 2


def _truncate_chars(
    text: str,
    max_chars: int,
    metrics: dict | None = None,
    metrics_key: str = "",
) -> str:
    """Hard-truncate text with a suffix marker. Optionally record stats into metrics."""
    if metrics is not None and metrics_key:
        metrics[f"{metrics_key}_chars_raw"] = len(text)
    if max_chars <= 0:
        if metrics is not None and metrics_key:
            metrics[f"{metrics_key}_chars_used"] = 0
            metrics[f"{metrics_key}_truncated"] = bool(text)
        return ""
    if len(text) <= max_chars:
        if metrics is not None and metrics_key:
            metrics[f"{metrics_key}_chars_used"] = len(text)
            metrics[f"{metrics_key}_truncated"] = False
        return text
    suffix = "... [truncated]"
    keep = max(0, max_chars - len(suffix))
    result = text[:keep].rstrip() + suffix
    if metrics is not None and metrics_key:
        metrics[f"{metrics_key}_chars_used"] = len(result)
        metrics[f"{metrics_key}_truncated"] = True
    return result


def _summarize_section(section_text: str) -> str:
    """Reduce a markdown section to its headers only (## lines), discarding body text."""
    lines = section_text.split("\n")
    headers = [line for line in lines if line.startswith("#")]
    if not headers:
        # No headers — keep first non-empty line as label
        for line in lines:
            if line.strip():
                return line.strip()
        return ""
    return "\n".join(headers)


def _smart_truncate_system_context(
    text: str,
    max_chars: int,
    metrics: dict | None = None,
) -> str:
    """Truncate system context by sections instead of cutting mid-text.

    The system context is built from multiple .md files joined by double newlines.
    When over budget, later sections are progressively compressed to their headers
    only, then dropped entirely if still over.  The first section (role definition)
    is always kept in full.  Falls back to hard truncation only if the first
    section alone exceeds the limit.
    """
    if metrics is not None:
        metrics["system_context_chars_raw"] = len(text)
    if max_chars <= 0:
        if metrics is not None:
            metrics["system_context_chars_used"] = 0
            metrics["system_context_truncated"] = False
            metrics["system_context_sections_summarized"] = 0
        return ""
    if len(text) <= max_chars:
        if metrics is not None:
            metrics["system_context_chars_used"] = len(text)
            metrics["system_context_truncated"] = False
            metrics["system_context_sections_summarized"] = 0
        return text

    # Split into sections on top-level headers (# ...).
    # Each file in system_context/ starts with a # header.
    sections: list[str] = []
    current_lines: list[str] = []
    for line in text.split("\n"):
        if line.startswith("# ") and not line.startswith("## ") and current_lines:
            sections.append("\n".join(current_lines))
            current_lines = [line]
        else:
            current_lines.append(line)
    if current_lines:
        sections.append("\n".join(current_lines))

    if len(sections) <= 1:
        # Single section — fall back to hard truncation
        result = _truncate_chars(text, max_chars)
        if metrics is not None:
            metrics["system_context_chars_used"] = len(result)
            metrics["system_context_truncated"] = True
            metrics["system_context_sections_summarized"] = 0
        return result

    # Phase 1: Compress sections from the end, replacing body with headers only.
    # Never compress the first section (role definition).
    result_sections = list(sections)
    sections_summarized = 0
    for i in range(len(result_sections) - 1, 0, -1):
        total = sum(len(s) for s in result_sections) + (len(result_sections) - 1) * 2
        if total <= max_chars:
            break
        summarized = _summarize_section(result_sections[i])
        if summarized:
            result_sections[i] = summarized
        else:
            result_sections.pop(i)
        sections_summarized += 1

    # Phase 2: If still over, drop compressed sections from the end.
    while len(result_sections) > 1:
        total = sum(len(s) for s in result_sections) + (len(result_sections) - 1) * 2
        if total <= max_chars:
            break
        result_sections.pop()
        sections_summarized += 1

    result = "\n\n".join(result_sections)

    # Phase 3: If the first section alone is too long, fall back to hard truncation.
    if len(result) > max_chars:
        result = _truncate_chars(result, max_chars)

    if metrics is not None:
        metrics["system_context_chars_used"] = len(result)
        metrics["system_context_truncated"] = True
        metrics["system_context_sections_summarized"] = sections_summarized

    return result


def _estimate_tokens(text: str) -> int:
    """Rough token estimate from character count (~4 chars per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


def _format_context_log_summary(metrics: dict) -> str:
    """Format pipeline metrics as a compact one-line log string."""
    parts = [
        f"tokens_est={metrics.get('total_tokens_est', '?')}",
        f"msgs={metrics.get('total_messages', '?')}",
        f"sys_trunc={'yes' if metrics.get('system_context_truncated') else 'no'}"
        + (f"({metrics.get('system_context_sections_summarized', 0)}sect)" if metrics.get('system_context_truncated') else ""),
        f"user_trunc={'yes' if metrics.get('user_context_truncated') else 'no'}",
        f"tool_rounds_omitted={metrics.get('tool_rounds_omitted', 0)}/{metrics.get('tool_rounds_total', 0)}",
        f"history={metrics.get('messages_before_history_trim', '?')}->{metrics.get('messages_after_history_trim', '?')}",
        f"conv_summary={'yes' if metrics.get('conversation_summary_injected') else 'no'}",
        f"provider={metrics.get('provider', '?')}",
        f"first_turn={'yes' if metrics.get('is_first_turn') else 'no'}",
    ]
    return " ".join(parts)


def _count_request_tokens(messages: list[dict]) -> int:
    """Estimate total input tokens from OpenAI-format messages."""
    total_chars = 0
    for m in messages:
        content = m.get("content")
        if isinstance(content, str):
            total_chars += len(content)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and "text" in part:
                    total_chars += len(str(part.get("text", "")))
    return _estimate_tokens("x" * total_chars) if total_chars else 0


def _summarize_tool_result(tool_name: str, result_content: str) -> str:
    """Generate a brief summary of a tool result to replace full content in older rounds.

    The assistant message (with tool_calls) is kept, so the LLM already sees
    what tool was called and with what arguments.  This summary captures
    the *outcome* so the model retains a minimal trace of what happened.
    """
    try:
        result = json.loads(result_content) if result_content else {}
    except (json.JSONDecodeError, TypeError):
        return json.dumps({"_summary": f"{tool_name}: result omitted"})

    if not isinstance(result, dict):
        return json.dumps({"_summary": f"{tool_name}: ok"})

    # Check success/error
    success = result.get("success")
    error = result.get("error", "")

    if success is False or error:
        error_msg = (str(error)[:80]) if error else "failed"
        return json.dumps({"_summary": f"{tool_name}: error — {error_msg}"})

    # For successful results, extract a few compact key-value pairs
    data = result.get("data", result)
    if isinstance(data, dict):
        summary_parts = []
        for key in ("nodeCount", "nodeId", "count", "total", "name", "slug", "status", "message"):
            if key in data:
                val = data[key]
                if isinstance(val, (str, int, float, bool)):
                    val_str = str(val)
                    if len(val_str) > 50:
                        val_str = val_str[:47] + "..."
                    summary_parts.append(f"{key}={val_str}")

        # Extract names from array fields (e.g. searchInstalledNodes nodes, research results)
        for key in ("nodes", "results", "items"):
            arr = data.get(key)
            if isinstance(arr, list) and arr:
                names = []
                for item in arr:
                    if isinstance(item, dict):
                        n = item.get("name") or item.get("title") or item.get("type", "")
                        if n:
                            names.append(str(n))
                if names:
                    MAX_LISTED = 8
                    listed = names[:MAX_LISTED]
                    tail = f", +{len(names) - MAX_LISTED} more" if len(names) > MAX_LISTED else ""
                    summary_parts.append(f"{key}=[{', '.join(listed)}{tail}]")
                break  # only include one array field

        if summary_parts:
            return json.dumps({"_summary": f"{tool_name}: ok ({', '.join(summary_parts[:4])})"})

    return json.dumps({"_summary": f"{tool_name}: ok"})


def _build_tool_name_map(
    messages: list[dict],
    rounds_to_summarize: list[tuple[int, list[int]]],
) -> dict[int, str]:
    """Map tool message indices to their tool names from the preceding assistant tool_calls."""
    tool_name_by_idx: dict[int, str] = {}
    for asst_idx, tool_indices in rounds_to_summarize:
        asst_msg = messages[asst_idx]
        call_names: dict[str, str] = {}
        for tc in asst_msg.get("tool_calls", []):
            if isinstance(tc, dict):
                tc_id = tc.get("id", "")
                func = tc.get("function", {})
                if isinstance(func, dict):
                    call_names[tc_id] = func.get("name", "unknown")
        for tidx in tool_indices:
            tc_id = messages[tidx].get("tool_call_id", "")
            tool_name_by_idx[tidx] = call_names.get(tc_id, "unknown")
    return tool_name_by_idx


def _trim_old_tool_results(
    messages: list[dict],
    keep_last_n_rounds: int,
    metrics: dict | None = None,
) -> list[dict]:
    """Replace content of tool results from older rounds with a brief summary.
    A 'round' is one assistant message with tool_calls plus the immediately following tool messages.
    Only the last keep_last_n_rounds rounds keep full content; older tool messages get a one-line
    summary (e.g. 'addNode: ok (nodeId=5)') so the model retains a trace of what happened."""
    if metrics is not None:
        metrics["messages_before_tool_trim"] = len(messages)

    # Build list of (assistant_idx, [tool_indices]) for each round.
    rounds: list[tuple[int, list[int]]] = []
    i = 0
    while i < len(messages):
        msg = messages[i]
        if msg.get("role") == "assistant" and msg.get("tool_calls"):
            tool_indices = []
            j = i + 1
            while j < len(messages) and messages[j].get("role") == "tool":
                tool_indices.append(j)
                j += 1
            rounds.append((i, tool_indices))
            i = j
        else:
            i += 1

    if not rounds:
        if metrics is not None:
            metrics["tool_rounds_total"] = 0
            metrics["tool_rounds_omitted"] = 0
        return list(messages)

    # Determine which rounds to keep vs summarize
    if keep_last_n_rounds <= 0:
        rounds_to_summarize = rounds
        rounds_to_keep_set: set[int] = set()
    else:
        rounds_to_summarize = rounds[:-keep_last_n_rounds] if keep_last_n_rounds < len(rounds) else []
        rounds_to_keep_set = set()
        for (_, indices) in rounds[-keep_last_n_rounds:]:
            rounds_to_keep_set.update(indices)

    if metrics is not None:
        metrics["tool_rounds_total"] = len(rounds)
        metrics["tool_rounds_omitted"] = len(rounds_to_summarize)

    if not rounds_to_summarize:
        return list(messages)

    # Build index → tool name map for rounds we'll summarize
    tool_name_by_idx = _build_tool_name_map(messages, rounds_to_summarize)

    out = []
    for idx, m in enumerate(messages):
        m = dict(m)
        if m.get("role") == "tool" and idx not in rounds_to_keep_set and idx in tool_name_by_idx:
            tool_name = tool_name_by_idx[idx]
            m["content"] = _summarize_tool_result(tool_name, m.get("content", ""))
        out.append(m)
    return out


def _build_conversation_summary(dropped: list[dict]) -> str:
    """Build a compact summary of dropped messages for context continuity.

    Extracts user requests, tool actions performed, and the last assistant
    context from messages that are being trimmed out of the conversation window.
    Returns empty string if there is nothing meaningful to summarize.
    """
    user_requests: list[str] = []
    tool_actions: list[str] = []
    last_assistant_text = ""

    for m in dropped:
        role = m.get("role")
        if role == "user":
            text = (m.get("content") or "").strip()
            if text and len(text) > 5:
                if len(text) > 120:
                    text = text[:117] + "..."
                user_requests.append(text)
        elif role == "assistant":
            for tc in m.get("tool_calls", []):
                if not isinstance(tc, dict):
                    continue
                func = tc.get("function", {})
                if not isinstance(func, dict):
                    continue
                name = func.get("name", "")
                if not name:
                    continue
                args_str = func.get("arguments", "{}")
                key_arg = ""
                try:
                    args_dict = json.loads(args_str) if isinstance(args_str, str) else {}
                    if isinstance(args_dict, dict):
                        for k, v in args_dict.items():
                            if isinstance(v, (str, int, float)) and str(v).strip():
                                val = str(v)
                                if len(val) > 30:
                                    val = val[:27] + "..."
                                key_arg = f"{k}={val}"
                                break
                except (json.JSONDecodeError, TypeError):
                    pass
                action = f"{name}({key_arg})" if key_arg else name
                tool_actions.append(action)
            text = (m.get("content") or "").strip()
            if text:
                last_assistant_text = text

    if not user_requests and not tool_actions:
        return ""

    parts = ["[Conversation summary — earlier messages were trimmed]"]
    if user_requests:
        recent = user_requests[-4:]
        parts.append("User requests: " + " → ".join(f'"{r}"' for r in recent))
    if tool_actions:
        parts.append("Actions taken: " + ", ".join(tool_actions[-8:]))
    if last_assistant_text:
        brief = last_assistant_text[:200]
        if len(last_assistant_text) > 200:
            brief += "..."
        parts.append("Last context: " + brief)

    return "\n".join(parts)


def _trim_openai_history(
    messages: list[dict],
    max_non_system_messages: int,
    metrics: dict | None = None,
) -> list[dict]:
    """Trim non-system history to a bounded tail while preserving system message(s).
    When messages are dropped, a conversation summary is injected for context continuity."""
    if metrics is not None:
        metrics["messages_before_history_trim"] = len(messages)

    if max_non_system_messages <= 0:
        result = [m for m in messages if m.get("role") == "system"]
        if metrics is not None:
            metrics["messages_after_history_trim"] = len(result)
            metrics["history_trimmed"] = len(result) < len(messages)
        return result

    system_messages = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    if len(non_system) <= max_non_system_messages:
        if metrics is not None:
            metrics["messages_after_history_trim"] = len(messages)
            metrics["history_trimmed"] = False
        return messages

    # Split into dropped prefix and kept tail
    dropped = non_system[:-max_non_system_messages]
    tail = non_system[-max_non_system_messages:]
    # Avoid starting with orphan tool results.
    while tail and tail[0].get("role") == "tool":
        tail = tail[1:]

    # Build summary of dropped messages and inject as system addendum
    summary_text = _build_conversation_summary(dropped)
    result = list(system_messages)
    if summary_text:
        result.append({"role": "system", "content": summary_text})
    result.extend(tail)

    if metrics is not None:
        metrics["messages_after_history_trim"] = len(result)
        metrics["history_trimmed"] = True
        metrics["conversation_summary_injected"] = bool(summary_text)
    return result


def _compact_messages_for_retry(
    messages: list[dict],
    attempt: int,
) -> list[dict]:
    """Apply progressively more aggressive compaction for 413/context-too-large retries.

    attempt=1: summarize ALL tool results (including recent ones).
    attempt=2: also halve history and further truncate system context.
    """
    messages = list(messages)

    if attempt >= 1:
        # Phase 1: summarize every tool result (keep_last_n_rounds=0)
        messages = _trim_old_tool_results(messages, keep_last_n_rounds=0)

    if attempt >= 2:
        # Phase 2: halve non-system history
        non_system_count = sum(1 for m in messages if m.get("role") != "system")
        messages = _trim_openai_history(
            messages, max(4, non_system_count // 2)
        )
        # Phase 2b: cut system context to half the normal budget
        for i, m in enumerate(messages):
            if m.get("role") == "system":
                content = m.get("content", "")
                cap = LLM_SYSTEM_CONTEXT_MAX_CHARS // 2
                if len(content) > cap:
                    messages[i] = {**m, "content": _smart_truncate_system_context(content, cap)}
                break

    return messages
