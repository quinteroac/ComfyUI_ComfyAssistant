"""Message format transformations between OpenAI, Anthropic, CLI, and UI formats."""

from __future__ import annotations

import json
import logging
import re
import uuid

from sse_streaming import _get_tool_name, _is_tool_ui_part
from tools_definitions import TOOLS

logger = logging.getLogger("ComfyUI_ComfyAssistant.message_transforms")

TOOLS_DEFINITIONS = TOOLS


def _stringify_message_content(content) -> str:
    """Best-effort string conversion for message content."""
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    try:
        return json.dumps(content, ensure_ascii=False)
    except Exception:
        return str(content)


def _openai_messages_to_cli_prompt(messages: list[dict]) -> str:
    """Build a plain transcript prompt for CLI-based providers."""
    blocks = []
    for message in messages:
        role = (message.get("role") or "user").upper()
        if role == "ASSISTANT" and message.get("tool_calls"):
            calls = []
            for tool_call in message.get("tool_calls", []):
                if not isinstance(tool_call, dict):
                    continue
                function = tool_call.get("function") or {}
                name = function.get("name", "")
                args = function.get("arguments", "{}")
                calls.append(f"{name}({args})")
            if calls:
                blocks.append(f"[ASSISTANT_TOOL_CALLS]\n" + "\n".join(calls))

        content = _stringify_message_content(message.get("content"))
        if content.strip():
            blocks.append(f"[{role}]\n{content}")

    transcript = "\n\n".join(blocks).strip()
    if not transcript:
        return "User: Hello"
    return transcript


def _cli_tool_specs() -> list[dict]:
    """Return compact tool specs for CLI prompt injection."""
    specs = []
    for tool in TOOLS_DEFINITIONS:
        if not isinstance(tool, dict):
            continue
        function = tool.get("function")
        if not isinstance(function, dict):
            continue
        name = function.get("name")
        if not name:
            continue
        specs.append({
            "name": name,
            "description": function.get("description", ""),
            "parameters": function.get("parameters", {"type": "object"}),
        })
    return specs


def _cli_response_schema() -> dict:
    """JSON schema expected from CLI providers."""
    return {
        "type": "object",
        "properties": {
            "text": {
                "type": "string",
                "description": "Assistant user-facing reply. Empty when only tool calls are needed.",
            },
            "tool_calls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "input_json": {
                            "type": "string",
                            "description": "JSON object encoded as string with tool input arguments.",
                        },
                    },
                    "required": ["name", "input_json"],
                    "additionalProperties": False,
                },
                "default": [],
            },
        },
        "required": ["text", "tool_calls"],
        "additionalProperties": False,
    }


def _build_cli_tool_prompt(messages: list[dict]) -> str:
    """Build CLI prompt including tool specs and strict response contract."""
    transcript = _openai_messages_to_cli_prompt(messages)
    tools_json = json.dumps(_cli_tool_specs(), ensure_ascii=False)

    # Check if the last message is a tool result
    has_recent_tool_results = any(
        m.get("role") == "tool" for m in messages[-3:] if messages
    )

    tool_usage_rule = (
        "- IMPORTANT: If the last messages are [TOOL] results, you MUST respond with text summarizing the results. DO NOT call more tools unless explicitly asked.\n"
        if has_recent_tool_results else
        "- If tools are needed, add one or more tool_calls.\n"
    )

    return (
        "You are ComfyUI Assistant backend provider adapter.\n"
        "Decide whether to answer normally or call tools.\n"
        "Return JSON only with this exact shape:\n"
        "{ \"text\": string, \"tool_calls\": [{\"name\": string, \"input_json\": string}] }\n"
        "Rules:\n"
        f"{tool_usage_rule}"
        "- If tool_calls is non-empty, keep text brief or empty.\n"
        "- Use only tool names from the provided tool list.\n"
        "- input_json must be a JSON string encoding an object that matches each tool parameter schema.\n\n"
        f"Available tools:\n{tools_json}\n\n"
        f"Conversation transcript:\n{transcript}\n"
    )


def _extract_json_from_text(text: str):
    """Extract first valid JSON object from text."""
    raw = (text or "").strip()
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    fenced = re.search(r"```json\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if fenced:
        try:
            return json.loads(fenced.group(1))
        except json.JSONDecodeError:
            pass

    start = raw.find("{")
    end = raw.rfind("}")
    if start >= 0 and end > start:
        candidate = raw[start:end + 1]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            return None
    return None


def _parse_cli_tool_calls(raw_calls, allowed_tool_names: set[str]) -> list[dict]:
    """Normalize tool call objects from CLI JSON output."""
    tool_calls = []
    if not isinstance(raw_calls, list):
        return tool_calls
    for call in raw_calls:
        if not isinstance(call, dict):
            continue
        name = call.get("name") or call.get("tool")
        if not isinstance(name, str) or not name:
            continue
        if name not in allowed_tool_names:
            continue
        input_value = {}
        input_json = call.get("input_json")
        if isinstance(input_json, str) and input_json.strip():
            try:
                input_value = json.loads(input_json)
            except json.JSONDecodeError:
                input_value = {}
        elif "input" in call:
            input_value = call.get("input", {})
            if isinstance(input_value, str):
                try:
                    input_value = json.loads(input_value)
                except json.JSONDecodeError:
                    input_value = {}
        if not isinstance(input_value, dict):
            input_value = {}
        tool_calls.append({"name": name, "input": input_value})
    return tool_calls


def _normalize_cli_structured_response(
    raw_text: str,
) -> tuple[str, list[dict]]:
    """Extract text + tool calls from CLI output (JSON-first, text fallback)."""
    allowed_tool_names = {
        function.get("name")
        for tool in TOOLS_DEFINITIONS
        if isinstance(tool, dict)
        for function in [tool.get("function")]
        if isinstance(function, dict) and function.get("name")
    }
    parsed = _extract_json_from_text(raw_text)
    if not isinstance(parsed, dict):
        return (raw_text.strip(), [])

    # claude_code CLI envelope: {"type": "result", "structured_output": {text, tool_calls}, "result": "..."}
    # Our schema is requested via --json-schema; the CLI puts it in structured_output (or result as JSON string).
    if parsed.get("type") == "result":
        inner = parsed.get("structured_output")
        if isinstance(inner, dict):
            text = inner.get("text", "")
            if not isinstance(text, str):
                text = ""
            calls = _parse_cli_tool_calls(inner.get("tool_calls", []), allowed_tool_names)
            return (text.strip(), calls)
        if parsed.get("result"):
            inner = _extract_json_from_text(
                parsed["result"] if isinstance(parsed["result"], str) else str(parsed["result"])
            )
            if isinstance(inner, dict):
                text = inner.get("text", "")
                if not isinstance(text, str):
                    text = ""
                calls = _parse_cli_tool_calls(inner.get("tool_calls", []), allowed_tool_names)
                return (text.strip(), calls)

    # Standard envelope: {"text": "...", "tool_calls": [...]}
    text = parsed.get("text", "")
    if not isinstance(text, str):
        text = ""
    calls = _parse_cli_tool_calls(parsed.get("tool_calls", []), allowed_tool_names)
    return (text.strip(), calls)


def _openai_tools_to_anthropic(tools: list[dict]) -> list[dict]:
    """Convert OpenAI function-tool schema to Anthropic tool schema."""
    anthropic_tools = []
    for tool in tools:
        if not isinstance(tool, dict):
            continue
        function = tool.get("function")
        if not isinstance(function, dict):
            continue
        name = function.get("name")
        if not name:
            continue
        anthropic_tools.append({
            "name": name,
            "description": function.get("description", ""),
            "input_schema": function.get("parameters", {"type": "object"})
        })
    return anthropic_tools


def _normalize_tool_result_content(content) -> str:
    """Normalize tool result content to a text payload for Anthropic."""
    if isinstance(content, str):
        return content
    try:
        return json.dumps(content)
    except Exception:
        return str(content)


def _merge_adjacent_anthropic_messages(messages: list[dict]) -> list[dict]:
    """Merge adjacent Anthropic messages with the same role."""
    if not messages:
        return []
    merged = [messages[0]]
    for message in messages[1:]:
        prev = merged[-1]
        if prev.get("role") == message.get("role"):
            prev_content = prev.get("content", [])
            next_content = message.get("content", [])
            if isinstance(prev_content, list) and isinstance(next_content, list):
                prev_content.extend(next_content)
                prev["content"] = prev_content
            else:
                merged.append(message)
        else:
            merged.append(message)
    return merged


def _openai_messages_to_anthropic(messages: list[dict]) -> tuple[str, list[dict]]:
    """Convert OpenAI-format messages to Anthropic Messages API format."""
    system_parts = []
    anthropic_messages = []

    for message in messages:
        role = message.get("role")

        if role == "system":
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                system_parts.append(content)
            continue

        if role == "user":
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                anthropic_messages.append({
                    "role": "user",
                    "content": [{"type": "text", "text": content}]
                })
            continue

        if role == "assistant":
            blocks = []
            content = message.get("content")
            if isinstance(content, str) and content.strip():
                blocks.append({"type": "text", "text": content})
            for tool_call in message.get("tool_calls", []) or []:
                if not isinstance(tool_call, dict):
                    continue
                function = tool_call.get("function", {}) or {}
                args = function.get("arguments", "{}")
                try:
                    tool_input = json.loads(args) if isinstance(args, str) else args
                except json.JSONDecodeError:
                    tool_input = {}
                blocks.append({
                    "type": "tool_use",
                    "id": tool_call.get("id", f"call_{uuid.uuid4().hex[:12]}"),
                    "name": function.get("name", ""),
                    "input": tool_input if isinstance(tool_input, dict) else {}
                })
            if blocks:
                anthropic_messages.append({
                    "role": "assistant",
                    "content": blocks
                })
            continue

        if role == "tool":
            tool_call_id = message.get("tool_call_id", "")
            content = _normalize_tool_result_content(message.get("content", ""))
            if tool_call_id:
                anthropic_messages.append({
                    "role": "user",
                    "content": [{
                        "type": "tool_result",
                        "tool_use_id": tool_call_id,
                        "content": content
                    }]
                })

    system_text = "\n\n".join(system_parts).strip()
    return system_text, _merge_adjacent_anthropic_messages(anthropic_messages)


def _ui_messages_to_openai(messages: list) -> list:
    """Convert AI SDK v6 UIMessage format to OpenAI API format.

    Handles:
    - Text messages (type='text')
    - AI SDK v6 tool invocations (type='tool-<name>' or 'dynamic-tool')
      with states: input-available, output-available, output-error
    - Legacy assistant-ui format (type='tool-call', type='tool-result')
      for backward compatibility
    """
    result = []
    for msg in messages or []:
        role = msg.get("role", "user")

        if role == "system":
            result.append({"role": "system", "content": _extract_content(msg)})

        elif role == "user":
            content = _extract_content(msg)
            if isinstance(content, str) and content.strip().startswith("/"):
                # Slash commands are handled locally; skip if they slip into the stream.
                continue
            result.append({"role": "user", "content": content})

        elif role == "assistant":
            parts = msg.get("parts", [])

            # Fallback: no parts, use plain content string
            if not parts:
                content = msg.get("content", "")
                if isinstance(content, str) and content:
                    result.append({"role": "assistant", "content": content})
                continue

            # Split accumulated parts into per-round OpenAI messages.
            # A new round starts when a text part appears after tool
            # invocations in the current round.
            tool_calls_seen: set[str] = set()
            tool_results_seen: set[str] = set()

            round_text = ""
            round_tool_calls: list[dict] = []
            round_tool_results: list[dict] = []
            round_has_tools = False  # True once we've seen a tool in this round

            def _flush_round() -> None:
                """Emit the current round's assistant + tool messages."""
                nonlocal round_text, round_tool_calls, round_tool_results, round_has_tools
                openai_msg: dict = {"role": "assistant"}
                if round_text:
                    openai_msg["content"] = round_text
                if round_tool_calls:
                    openai_msg["tool_calls"] = round_tool_calls
                if "content" in openai_msg or "tool_calls" in openai_msg:
                    result.append(openai_msg)
                result.extend(round_tool_results)
                # Reset for next round
                round_text = ""
                round_tool_calls = []
                round_tool_results = []
                round_has_tools = False

            for part in parts:
                if not isinstance(part, dict):
                    continue

                part_type = part.get("type", "")

                if part_type == "text":
                    text = part.get("text", "")
                    if text:
                        # New text after tool invocations → close current round
                        if round_has_tools:
                            _flush_round()
                        round_text += text

                elif _is_tool_ui_part(part):
                    tool_name = _get_tool_name(part)
                    tool_call_id = part.get("toolCallId", "")
                    state = part.get("state", "")
                    args = part.get("input", {})

                    if tool_call_id and tool_call_id not in tool_calls_seen:
                        tool_calls_seen.add(tool_call_id)
                        round_tool_calls.append({
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(args) if args else "{}"
                            }
                        })

                    if state == "output-available" and "output" in part:
                        if tool_call_id and tool_call_id not in tool_results_seen:
                            tool_results_seen.add(tool_call_id)
                            round_tool_results.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(part.get("output", {}))
                            })
                    elif state == "output-error":
                        if tool_call_id and tool_call_id not in tool_results_seen:
                            tool_results_seen.add(tool_call_id)
                            round_tool_results.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps({
                                    "error": part.get("errorText", "Unknown error")
                                })
                            })

                    round_has_tools = True

                # Legacy format: type == 'tool-call'
                elif part_type == "tool-call":
                    tid = part.get("toolCallId", "")
                    if tid and tid not in tool_calls_seen:
                        tool_calls_seen.add(tid)
                        round_tool_calls.append({
                            "id": tid,
                            "type": "function",
                            "function": {
                                "name": part.get("toolName", ""),
                                "arguments": json.dumps(part.get("args", {}))
                            }
                        })
                    round_has_tools = True

            # Flush the final round
            _flush_round()

        elif role == "tool":
            # Legacy format: separate tool role messages
            parts = msg.get("parts", [])
            for part in parts:
                if isinstance(part, dict) and part.get("type") == "tool-result":
                    result.append({
                        "role": "tool",
                        "tool_call_id": part.get("toolCallId", ""),
                        "content": json.dumps(part.get("result", {}))
                    })

    return result


def _extract_content(msg: dict) -> str:
    """Extract text content from a UIMessage (parts array with type='text')."""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    parts = msg.get("parts", [])
    if not parts:
        return ""
    texts = []
    for p in parts:
        if isinstance(p, dict) and p.get("type") == "text":
            texts.append(p.get("text", ""))
    return "".join(texts) if texts else ""
