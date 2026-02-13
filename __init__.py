import asyncio
import os
import json
import logging
import uuid
import re
import shutil
import tempfile
import server
from aiohttp import web, ClientSession
import folder_paths
import nodes
import importlib

# Debug: log LLM request/response (set to logging.INFO to disable)
logger = logging.getLogger("ComfyUI_ComfyAssistant.chat")
# Default to INFO; allow override via env for debugging.
_log_level = os.getenv("COMFY_ASSISTANT_LOG_LEVEL", "INFO").upper()
logger.setLevel(getattr(logging, _log_level, logging.INFO))

# Import from current directory
current_dir = os.path.dirname(__file__)
import sys
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import agent_prompts
from agent_prompts import get_system_message
import user_context_store
import environment_scanner
import skill_manager
import documentation_resolver
import api_handlers
import conversation_logger
from tools_definitions import TOOLS


# Load .env from extension folder
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

NODE_CLASS_MAPPINGS = {}
__all__ = ["NODE_CLASS_MAPPINGS"]

# Define the path to our extension
workspace_path = os.path.dirname(__file__)
dist_path = os.path.join(workspace_path, "dist/example_ext")
dist_locales_path = os.path.join(workspace_path, "dist/locales")
user_context_path = os.path.join(workspace_path, "user_context")
system_context_path = os.path.join(workspace_path, "system_context")
user_context_store.set_user_context_path(user_context_path)

# LLM config from .env
LLM_PROVIDER = (os.environ.get("LLM_PROVIDER", "") or "").strip().lower()

# OpenAI-compatible provider
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "")
if not OPENAI_MODEL:
    OPENAI_MODEL = "gpt-4o-mini"
OPENAI_API_BASE_URL = os.environ.get(
    "OPENAI_API_BASE_URL",
    "https://api.openai.com/v1",
).rstrip("/")

# Anthropic provider (supports API key or Claude Code auth token)
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
ANTHROPIC_AUTH_TOKEN = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
ANTHROPIC_MODEL = os.environ.get("ANTHROPIC_MODEL", "")
if not ANTHROPIC_MODEL:
    ANTHROPIC_MODEL = "claude-sonnet-4-5"
ANTHROPIC_BASE_URL = os.environ.get(
    "ANTHROPIC_BASE_URL",
    "https://api.anthropic.com",
).rstrip("/")
try:
    ANTHROPIC_MAX_TOKENS = int(os.environ.get("ANTHROPIC_MAX_TOKENS", "4096"))
except ValueError:
    ANTHROPIC_MAX_TOKENS = 4096

# CLI-backed providers
CLAUDE_CODE_COMMAND = os.environ.get("CLAUDE_CODE_COMMAND", "claude")
CLAUDE_CODE_MODEL = os.environ.get("CLAUDE_CODE_MODEL", "")
CODEX_COMMAND = os.environ.get("CODEX_COMMAND", "codex")
CODEX_MODEL = os.environ.get("CODEX_MODEL", "")
GEMINI_CLI_COMMAND = os.environ.get("GEMINI_CLI_COMMAND", "gemini")
GEMINI_CLI_MODEL = os.environ.get("GEMINI_CLI_MODEL", "")
try:
    CLI_PROVIDER_TIMEOUT_SECONDS = int(
        os.environ.get("CLI_PROVIDER_TIMEOUT_SECONDS", "180")
    )
except ValueError:
    CLI_PROVIDER_TIMEOUT_SECONDS = 180

# Delay in seconds before each LLM request to avoid rate limits (e.g. 429)
LLM_REQUEST_DELAY_SECONDS = float(
    os.environ.get("LLM_REQUEST_DELAY_SECONDS", "1.0")
)


def _read_int_env(name: str, default: int) -> int:
    """Read int env var with a safe fallback."""
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


LLM_SYSTEM_CONTEXT_MAX_CHARS = _read_int_env(
    "LLM_SYSTEM_CONTEXT_MAX_CHARS", 12000
)
LLM_USER_CONTEXT_MAX_CHARS = _read_int_env(
    "LLM_USER_CONTEXT_MAX_CHARS", 2500
)
LLM_HISTORY_MAX_MESSAGES = _read_int_env(
    "LLM_HISTORY_MAX_MESSAGES", 24
)
# Keep full tool result content only for the last N "rounds" (each round = one assistant tool_calls + its tool replies). Older rounds get a short placeholder to avoid context growth.
LLM_TOOL_RESULT_KEEP_LAST_ROUNDS = _read_int_env(
    "LLM_TOOL_RESULT_KEEP_LAST_ROUNDS", 2
)

# Enable conversation logging in user_context/logs/
COMFY_ASSISTANT_ENABLE_LOGS = os.environ.get(
    "COMFY_ASSISTANT_ENABLE_LOGS", ""
).strip().lower() in ("1", "true", "yes")

# Debug: emit context-pipeline metrics in logs, headers, and SSE events.
# Enabled per-request via ?debug=context or always-on via this env var.
COMFY_ASSISTANT_DEBUG_CONTEXT = os.environ.get(
    "COMFY_ASSISTANT_DEBUG_CONTEXT", ""
).strip().lower() in ("1", "true", "yes")

# Maximum automatic compaction retries when the LLM returns 413 / context-too-large.
_MAX_CONTEXT_COMPACT_RETRIES = 2

# AI SDK UI Message Stream headers (required by AssistantChatTransport)
UI_MESSAGE_STREAM_HEADERS = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Vercel-AI-UI-Message-Stream": "v1",
}

# Tools definitions: imported from tools_definitions.py (single source of truth)
TOOLS_DEFINITIONS = TOOLS


def _sse_line(data):
    """Format a JSON object as an SSE data line."""
    return f"data: {json.dumps(data)}\n\n"


def _has_anthropic_credentials() -> bool:
    """Return True when Anthropic API key auth is available."""
    return bool(ANTHROPIC_API_KEY)


def _has_cli_provider_command(provider: str) -> bool:
    """Return True when provider CLI binary is available in PATH."""
    commands = {
        "claude_code": CLAUDE_CODE_COMMAND,
        "codex": CODEX_COMMAND,
        "gemini_cli": GEMINI_CLI_COMMAND,
    }
    command = commands.get(provider)
    return bool(command) and shutil.which(command) is not None


def _selected_llm_provider() -> str:
    """Resolve active provider from env and available credentials."""
    if LLM_PROVIDER in {"openai", "anthropic", "claude_code", "codex", "gemini_cli"}:
        return LLM_PROVIDER
    if OPENAI_API_KEY:
        return "openai"
    if _has_anthropic_credentials():
        return "anthropic"
    return "openai"


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


async def _run_cli_command(
    cmd: list[str],
    timeout_seconds: int,
) -> tuple[int, str, str, bool]:
    """Run a CLI command with timeout, returning rc/stdout/stderr/timed_out."""
    process = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, stderr = await asyncio.wait_for(
            process.communicate(),
            timeout=timeout_seconds,
        )
        out_str = stdout.decode("utf-8", errors="replace")
        err_str = stderr.decode("utf-8", errors="replace")
        rc = process.returncode or 0
        return (rc, out_str, err_str, False)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()
        return (124, "", f"Timed out after {timeout_seconds}s", True)


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
    return (
        "You are ComfyUI Assistant backend provider adapter.\n"
        "Decide whether to answer normally or call tools.\n"
        "Return JSON only with this exact shape:\n"
        "{ \"text\": string, \"tool_calls\": [{\"name\": string, \"input_json\": string}] }\n"
        "Rules:\n"
        "- If tools are needed, add one or more tool_calls.\n"
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


def _stream_ai_sdk_text(text: str, message_id: str):
    """Generate AI SDK Data Stream protocol chunks for a simple text message."""
    text_id = f"msg_{uuid.uuid4().hex[:24]}"
    yield _sse_line({"type": "start", "messageId": message_id})
    yield _sse_line({"type": "text-start", "id": text_id})
    if text:
        yield _sse_line({"type": "text-delta", "id": text_id, "delta": text})
    yield _sse_line({"type": "text-end", "id": text_id})
    yield _sse_line({"type": "finish", "finishReason": "stop"})
    yield "data: [DONE]\n\n"


def _is_tool_ui_part(part: dict) -> bool:
    """Check if a message part is a tool invocation (AI SDK v6 format).
    Static tools have type 'tool-<name>', dynamic tools have type 'dynamic-tool'."""
    part_type = part.get("type", "")
    return part_type.startswith("tool-") or part_type == "dynamic-tool"


def _get_tool_name(part: dict) -> str:
    """Extract tool name from a tool UI part."""
    part_type = part.get("type", "")
    if part_type == "dynamic-tool":
        return part.get("toolName", "")
    # Static: type is 'tool-<name>', extract everything after first 'tool-'
    return "-".join(part_type.split("-")[1:])


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


def _openai_message_content_to_str(msg: dict) -> str:
    """Extract plain text content from an OpenAI-format message."""
    content = msg.get("content")
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(
            str(p.get("text", "")) for p in content if isinstance(p, dict)
        )
    return ""


def _set_openai_message_content(msg: dict, text: str) -> None:
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


def _is_context_too_large_error(exc: Exception) -> bool:
    """Return True if the exception signals that the request payload / context is too large."""
    status = getattr(exc, "status_code", None) or (
        getattr(getattr(exc, "response", None), "status_code", None)
    )
    if status == 413:
        return True
    # OpenAI and many compatible providers return 400 for context_length_exceeded
    if status == 400:
        msg = str(exc).lower()
        for pattern in (
            "context length",
            "maximum context",
            "token limit",
            "too many tokens",
            "payload too large",
            "content_length",
            "context_length",
            "max_tokens",
            "input too long",
        ):
            if pattern in msg:
                return True
    return False


def _is_context_too_large_response(status: int, body: str) -> bool:
    """Return True if an HTTP response status+body indicates context too large (Anthropic path)."""
    if status == 413:
        return True
    if status == 400:
        lower = body.lower()
        for pattern in (
            "context length",
            "input too long",
            "too many tokens",
            "token limit",
            "payload too large",
            "max_tokens",
        ):
            if pattern in lower:
                return True
    return False


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


# Print the current paths for debugging
print(f"ComfyUI_example_frontend_extension workspace path: {workspace_path}")
print(f"Dist path: {dist_path}")
print(f"Dist locales path: {dist_locales_path}")
print(f"Locales exist: {os.path.exists(dist_locales_path)}")


def _parse_thinking_tags(text: str) -> tuple[list, str]:
    """Parse <think> tags from text and return reasoning parts + cleaned text."""
    import re

    reasoning_parts = []
    # Find all <think>...</think> blocks
    think_pattern = r'<think>(.*?)</think>'
    matches = re.finditer(think_pattern, text, re.DOTALL)

    for match in matches:
        thinking_text = match.group(1).strip()
        if thinking_text:
            reasoning_parts.append(thinking_text)

    # Remove all <think> tags from text
    cleaned_text = re.sub(think_pattern, '', text, flags=re.DOTALL).strip()

    return reasoning_parts, cleaned_text


def _get_last_user_text(messages: list) -> str:
    """Extract the most recent user text from UI messages."""
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        if isinstance(content, list):
            parts = []
            for part in content:
                if isinstance(part, dict) and part.get("type") == "text":
                    text = part.get("text")
                    if text:
                        parts.append(text)
            return "".join(parts)
        return ""
    return ""


def _get_last_openai_user_text(messages: list) -> str:
    """Extract the most recent user content from OpenAI-format messages."""
    for msg in reversed(messages):
        if msg.get("role") != "user":
            continue
        content = msg.get("content")
        if isinstance(content, str):
            return content
        return ""
    return ""


async def chat_api_handler(request: web.Request) -> web.Response:
    """Handle POST /api/chat. Uses an OpenAI-compatible provider when API key is set.
    Returns AI SDK UI Message Stream format for AssistantChatTransport."""
    try:
        body = await request.json() if request.body_exists else {}
    except json.JSONDecodeError:
        return web.json_response(
            {"error": "Invalid JSON body"},
            status=400,
        )
    messages = body.get("messages", [])
    # If the last message is a local slash response, do not call the LLM.
    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, dict) and last_msg.get("role") == "assistant":
            content = _extract_content(last_msg)
            if isinstance(content, str) and "<!-- local:slash -->" in content:
                async def stream_empty():
                    yield _sse_line({"type": "start", "messageId": f"msg_{uuid.uuid4().hex}"}).encode("utf-8")
                    yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
                    yield "data: [DONE]\n\n".encode("utf-8")

                resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
                await resp.prepare(request)
                async for chunk in stream_empty():
                    await resp.write(chunk)
                return resp
    openai_messages = _ui_messages_to_openai(messages)

    # Context pipeline metrics (collected throughout the handler)
    metrics: dict = {}
    debug_context = COMFY_ASSISTANT_DEBUG_CONTEXT or (
        request.query.get("debug") == "context"
    )

    # Reload agent_prompts to pick up any changes (useful during development)
    importlib.reload(agent_prompts)
    from agent_prompts import get_system_message, get_system_message_continuation
    import user_context_loader

    # Add system message if not present. Send full context only on first turn to avoid
    # re-sending the same long context on every request; use short continuation otherwise.
    has_system = any(msg.get("role") == "system" for msg in openai_messages)
    has_prior_assistant = any(msg.get("role") == "assistant" for msg in openai_messages)
    metrics["is_first_turn"] = not has_prior_assistant

    # Reload agent_prompts to pick up any changes (useful during development)
    importlib.reload(agent_prompts)
    from agent_prompts import get_system_message, get_system_message_continuation
    import user_context_loader

    if not has_system:
        system_context_text = ""
        user_context = None
        environment_summary = ""
        user_skills_list = []
        try:
            user_skills_list = skill_manager.list_skills()
            environment_summary = user_context_loader.load_environment_summary()
        except Exception:
            pass

        if has_prior_assistant:
            openai_messages.insert(0, get_system_message_continuation(
                user_skills=user_skills_list,
                environment_summary=environment_summary
            ))
        else:
            try:
                system_context_text = user_context_loader.load_system_context(system_context_path)
                user_context = user_context_loader.load_user_context()
            except Exception:
                pass
            system_context_text = _smart_truncate_system_context(
                system_context_text,
                LLM_SYSTEM_CONTEXT_MAX_CHARS,
                metrics=metrics,
            )
            if not (system_context_text or "").strip():
                system_context_text = (
                    "You are ComfyUI Assistant. Help users with ComfyUI workflows. "
                    "Use getWorkflowInfo, addNode, removeNode, connectNodes, setNodeWidgetValue, fillPromptNode when needed. "
                    "Reply in the user's language. For greetings only, reply with text; do not call tools."
                )
            openai_messages.insert(
                0,
                get_system_message(
                    system_context_text,
                    user_context,
                    environment_summary,
                    user_context_max_chars=LLM_USER_CONTEXT_MAX_CHARS,
                    user_skills=user_skills_list,
                    metrics=metrics,
                ),
            )
    # Handle /skill <name>: resolve skill and inject into this turn; replace user message
    _inject_skill_if_slash_skill(openai_messages)
    # Keep full tool results only for the last N rounds; older ones get a short placeholder
    openai_messages = _trim_old_tool_results(
        openai_messages,
        LLM_TOOL_RESULT_KEEP_LAST_ROUNDS,
        metrics=metrics,
    )
    openai_messages = _trim_openai_history(
        openai_messages,
        LLM_HISTORY_MAX_MESSAGES,
        metrics=metrics,
    )

    message_id = f"msg_{uuid.uuid4().hex}"
    selected_provider = _selected_llm_provider()

    if selected_provider == "claude_code":
        placeholder = (
            f"Chat API is not configured. Install `{CLAUDE_CODE_COMMAND}` "
            "or set CLAUDE_CODE_COMMAND to the correct executable."
        )
        has_provider_credentials = _has_cli_provider_command("claude_code")
    elif selected_provider == "codex":
        placeholder = (
            f"Chat API is not configured. Install `{CODEX_COMMAND}` "
            "or set CODEX_COMMAND to the correct executable."
        )
        has_provider_credentials = _has_cli_provider_command("codex")
    elif selected_provider == "gemini_cli":
        placeholder = (
            f"Chat API is not configured. Install `{GEMINI_CLI_COMMAND}` "
            "or set GEMINI_CLI_COMMAND to the correct executable."
        )
        has_provider_credentials = _has_cli_provider_command("gemini_cli")
    elif selected_provider == "anthropic":
        if ANTHROPIC_AUTH_TOKEN and not ANTHROPIC_API_KEY:
            placeholder = (
                "ANTHROPIC_AUTH_TOKEN from `claude setup-token` cannot "
                "authenticate api.anthropic.com/v1/messages in this backend. "
                "Set ANTHROPIC_API_KEY in .env."
            )
        else:
            placeholder = (
                "Chat API is not configured. Set ANTHROPIC_API_KEY in .env."
            )
        has_provider_credentials = _has_anthropic_credentials()
    else:
        placeholder = (
            "Chat API is not configured. Set OPENAI_API_KEY in .env "
            "(copy from .env.example)."
        )
        has_provider_credentials = bool(OPENAI_API_KEY)

    if not has_provider_credentials:
        async def stream_placeholder():
            for chunk in _stream_ai_sdk_text(placeholder, message_id):
                yield chunk.encode("utf-8")
        resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
        await resp.prepare(request)
        async for chunk in stream_placeholder():
            await resp.write(chunk)
        return resp

    # Slash commands are handled client-side, except /skill <name> which is handled in the backend.
    raw_last_user = _get_last_user_text(messages).strip()
    if raw_last_user.startswith("/") and not raw_last_user.strip().lower().startswith("/skill"):
        async def stream_empty():
            yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")

        resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
        await resp.prepare(request)
        async for chunk in stream_empty():
            await resp.write(chunk)
        return resp
    # If no user message remains after filtering, do not call the LLM.
    last_user_text = _get_last_openai_user_text(openai_messages).strip()
    if not last_user_text:
        async def stream_empty():
            yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")

        resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
        await resp.prepare(request)
        async for chunk in stream_empty():
            await resp.write(chunk)
        return resp

    request_tokens_est = _count_request_tokens(openai_messages)
    metrics["total_messages"] = len(openai_messages)
    metrics["total_chars"] = sum(
        len(m.get("content", "")) if isinstance(m.get("content"), str) else 0
        for m in openai_messages
    )
    metrics["total_tokens_est"] = request_tokens_est
    metrics["provider"] = selected_provider
    logger.info(
        "[ComfyAssistant] context: %s",
        _format_context_log_summary(metrics),
    )
    logger.debug(
        "[ComfyAssistant] context metrics: %s",
        json.dumps(metrics, default=str),
    )

    # Prepare response headers (add debug header when enabled)
    if debug_context:
        response_headers = dict(UI_MESSAGE_STREAM_HEADERS)
        header_metrics = {
            k: metrics[k] for k in (
                "total_tokens_est", "total_messages", "total_chars",
                "system_context_truncated", "user_context_truncated",
                "tool_rounds_omitted", "tool_rounds_total",
                "history_trimmed", "conversation_summary_injected",
                "is_first_turn", "provider",
            ) if k in metrics
        }
        response_headers["X-ComfyAssistant-Context-Debug"] = json.dumps(
            header_metrics, separators=(",", ":")
        )
    else:
        response_headers = UI_MESSAGE_STREAM_HEADERS

    async def stream_openai():
        # Call an OpenAI-compatible API and stream response.
        from openai import AsyncOpenAI
        # Limit retries on 429 so we fail fast and show a clear message instead of long waits.
        client = AsyncOpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE_URL,
            max_retries=2,
        )

        text_id = f"msg_{uuid.uuid4().hex[:24]}"
        reasoning_id = None
        buffer = ""
        reasoning_sent = False
        text_sent = False  # True once we have sent at least one text-delta (so UI shows a message)
        text_start_emitted = False  # True after we emit text-start (only once per message)
        text_end_sent = False  # True after we emit text-end (must be before tool-input-available for client)
        # Buffer for accumulating tool call chunks
        tool_calls_buffer = {}
        # Accumulate assistant response for debug log
        response_text_parts = []
        response_tool_calls = []
        # Capture finish_reason and usage from the LLM streaming response (last chunk)
        llm_finish_reason = None
        usage_prompt_tokens = None
        usage_completion_tokens = None

        yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

        try:
            await asyncio.sleep(LLM_REQUEST_DELAY_SECONDS)

            # Retry with automatic compaction on 413 / context-too-large
            retry_messages = openai_messages
            stream = None
            for _compact_attempt in range(_MAX_CONTEXT_COMPACT_RETRIES + 1):
                try:
                    stream = await client.chat.completions.create(
                        model=OPENAI_MODEL,
                        messages=retry_messages,
                        tools=TOOLS_DEFINITIONS,
                        tool_choice="auto",
                        stream=True,
                    )
                    break  # create() succeeded
                except Exception as create_exc:
                    if _compact_attempt < _MAX_CONTEXT_COMPACT_RETRIES and _is_context_too_large_error(create_exc):
                        logger.warning(
                            "[ComfyAssistant] context too large (compact attempt %d/%d), "
                            "applying automatic compaction...",
                            _compact_attempt + 1,
                            _MAX_CONTEXT_COMPACT_RETRIES,
                        )
                        retry_messages = _compact_messages_for_retry(
                            retry_messages, _compact_attempt + 1
                        )
                        new_est = _count_request_tokens(retry_messages)
                        logger.info(
                            "[ComfyAssistant] compacted: %d messages, ~%d tokens (was ~%d)",
                            len(retry_messages),
                            new_est,
                            request_tokens_est,
                        )
                        continue
                    raise  # non-retryable or final attempt — propagate to outer handler

            async for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue

                # Last chunk may carry finish_reason and usage
                if choice.finish_reason:
                    llm_finish_reason = choice.finish_reason
                if getattr(chunk, "usage", None):
                    u = chunk.usage
                    if getattr(u, "prompt_tokens", None) is not None:
                        usage_prompt_tokens = u.prompt_tokens
                    if getattr(u, "completion_tokens", None) is not None:
                        usage_completion_tokens = u.completion_tokens

                delta = choice.delta
                
                # Handle text content
                if delta.content:
                    buffer += delta.content

                    # Check if we have complete thinking blocks
                    if '<think>' in buffer and '</think>' in buffer:
                        reasoning_parts, cleaned_text = _parse_thinking_tags(buffer)

                        # Send reasoning parts
                        for reasoning_text in reasoning_parts:
                            if not reasoning_sent:
                                reasoning_id = f"reasoning_{uuid.uuid4().hex[:24]}"
                                yield _sse_line({"type": "reasoning-start", "id": reasoning_id}).encode("utf-8")
                                reasoning_sent = True
                            yield _sse_line({"type": "reasoning-delta", "id": reasoning_id, "delta": reasoning_text}).encode("utf-8")

                        if reasoning_sent and reasoning_id:
                            yield _sse_line({"type": "reasoning-end", "id": reasoning_id}).encode("utf-8")
                            reasoning_sent = False

                        # Start text part for cleaned content (only once)
                        if cleaned_text and not text_start_emitted:
                            yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                            text_start_emitted = True

                        if cleaned_text:
                            yield _sse_line({"type": "text-delta", "id": text_id, "delta": cleaned_text}).encode("utf-8")
                            text_sent = True
                            response_text_parts.append(cleaned_text)

                        buffer = ""
                    else:
                        # Stream normally if no complete thinking blocks yet
                        if not '<think>' in buffer:
                            if not text_start_emitted:
                                yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                                text_start_emitted = True
                            yield _sse_line({"type": "text-delta", "id": text_id, "delta": delta.content}).encode("utf-8")
                            text_sent = True
                            response_text_parts.append(delta.content)
                            buffer = ""
                
                # Handle tool calls (Data Stream Protocol format)
                if delta.tool_calls:
                    for tool_call_delta in delta.tool_calls:
                        index = tool_call_delta.index
                        
                        # Initialize tool call buffer if needed
                        if index not in tool_calls_buffer:
                            tool_calls_buffer[index] = {
                                "id": "",
                                "name": "",
                                "arguments": "",
                                "completed": False,
                            }
                        tool_call_data = tool_calls_buffer[index]
                        if tool_call_delta.id:
                            tool_call_data["id"] = tool_call_delta.id
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_call_data["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                tool_call_data["arguments"] += tool_call_delta.function.arguments
                        # Do not emit tool-input-start / tool-input-delta here. Emitting
                        # only tool-input-available at the end avoids duplicate keys in
                        # assistant-ui (Duplicate key toolCallId-... in tapResources),
                        # which can occur when the client processes tool-input-available
                        # before the part from tool-input-start is committed.

            # Process any remaining buffer
            if buffer:
                reasoning_parts, cleaned_text = _parse_thinking_tags(buffer)

                for reasoning_text in reasoning_parts:
                    reasoning_id = f"reasoning_{uuid.uuid4().hex[:24]}"
                    yield _sse_line({"type": "reasoning-start", "id": reasoning_id}).encode("utf-8")
                    yield _sse_line({"type": "reasoning-delta", "id": reasoning_id, "delta": reasoning_text}).encode("utf-8")
                    yield _sse_line({"type": "reasoning-end", "id": reasoning_id}).encode("utf-8")

                if cleaned_text:
                    if not text_start_emitted:
                        yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                        text_start_emitted = True
                    yield _sse_line({"type": "text-delta", "id": text_id, "delta": cleaned_text}).encode("utf-8")
                    text_sent = True
                    response_text_parts.append(cleaned_text)

            # Do NOT emit placeholder text when model returns only tool calls.
            # assistant-ui already renders tool-call parts, so the UI won't be empty.

            # Close text part before tool calls so the client can finalize the message and run tools
            if text_sent and text_id and not text_end_sent:
                yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
                text_end_sent = True

            # Emit tool-input-available for all complete tool calls
            for index, tool_call in tool_calls_buffer.items():
                if tool_call["id"] and tool_call["name"] and tool_call["arguments"] and not tool_call["completed"]:
                    try:
                        args = json.loads(tool_call["arguments"])
                        response_tool_calls.append({"name": tool_call["name"], "input": args})
                        yield _sse_line({
                            "type": "tool-input-available",
                            "toolCallId": tool_call["id"],
                            "toolName": tool_call["name"],
                            "input": args
                        }).encode("utf-8")
                        tool_call["completed"] = True
                    except json.JSONDecodeError:
                        # JSON not valid yet, skip
                        pass

            # Token count for this request (real usage or estimate)
            out_tokens = usage_completion_tokens
            if out_tokens is None:
                out_tokens = _estimate_tokens("".join(response_text_parts))
            in_tokens = usage_prompt_tokens if usage_prompt_tokens is not None else request_tokens_est
            logger.info(
                "[ComfyAssistant] tokens in=%s out=%s provider=openai",
                in_tokens,
                out_tokens,
            )

        except Exception as e:
            logger.debug("LLM request failed: %s", e, exc_info=True)
            status = getattr(e, "status_code", None) or (
                getattr(getattr(e, "response", None), "status_code", None)
            )
            if status == 429:
                yield _sse_line({
                    "type": "error",
                    "errorText": "Rate limit exceeded (429). Please wait a minute and try again.",
                }).encode("utf-8")
            elif _is_context_too_large_error(e):
                yield _sse_line({
                    "type": "error",
                    "errorText": (
                        "Context too large for the model even after automatic compaction. "
                        "Try starting a new conversation or reducing history."
                    ),
                }).encode("utf-8")
            else:
                yield _sse_line({"type": "error", "errorText": str(e)}).encode("utf-8")

        if text_sent and text_id and not text_end_sent:
            yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
        # Map OpenAI finish_reason to AI SDK format (underscore → hyphen)
        finish_reason_map = {
            "stop": "stop",
            "tool_calls": "tool-calls",
            "length": "length",
            "content_filter": "content-filter",
        }
        ai_finish = finish_reason_map.get(llm_finish_reason or "stop", "stop")
        yield _sse_line({"type": "finish", "finishReason": ai_finish}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")

    async def stream_anthropic():
        text_id = f"msg_{uuid.uuid4().hex[:24]}"
        text_sent = False
        text_start_emitted = False
        text_end_sent = False
        response_text_parts = []
        response_tool_calls = []
        pending_tool_calls = []
        ai_finish = "stop"

        yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01",
        }
        headers["x-api-key"] = ANTHROPIC_API_KEY

        try:
            await asyncio.sleep(LLM_REQUEST_DELAY_SECONDS)

            # Retry with automatic compaction on 413 / context-too-large
            retry_messages = openai_messages
            api_data = None  # parsed JSON response on success
            for _compact_attempt in range(_MAX_CONTEXT_COMPACT_RETRIES + 1):
                system_text, anthropic_messages = _openai_messages_to_anthropic(
                    retry_messages
                )
                payload = {
                    "model": ANTHROPIC_MODEL,
                    "max_tokens": ANTHROPIC_MAX_TOKENS,
                    "messages": anthropic_messages,
                    "tools": _openai_tools_to_anthropic(TOOLS_DEFINITIONS),
                    "tool_choice": {"type": "auto"},
                }
                if system_text:
                    payload["system"] = system_text

                async with ClientSession() as session:
                    async with session.post(
                        f"{ANTHROPIC_BASE_URL}/v1/messages",
                        headers=headers,
                        json=payload,
                    ) as response:
                        response_text = await response.text()

                        # Check for context-too-large and retry with compaction
                        if _is_context_too_large_response(response.status, response_text):
                            if _compact_attempt < _MAX_CONTEXT_COMPACT_RETRIES:
                                logger.warning(
                                    "[ComfyAssistant] context too large (compact attempt %d/%d), "
                                    "applying automatic compaction...",
                                    _compact_attempt + 1,
                                    _MAX_CONTEXT_COMPACT_RETRIES,
                                )
                                retry_messages = _compact_messages_for_retry(
                                    retry_messages, _compact_attempt + 1
                                )
                                new_est = _count_request_tokens(retry_messages)
                                logger.info(
                                    "[ComfyAssistant] compacted: %d messages, ~%d tokens (was ~%d)",
                                    len(retry_messages),
                                    new_est,
                                    request_tokens_est,
                                )
                                continue
                            # Exhausted retries — show user-friendly error
                            yield _sse_line({
                                "type": "error",
                                "errorText": (
                                    "Context too large for the model even after automatic compaction. "
                                    "Try starting a new conversation or reducing history."
                                ),
                            }).encode("utf-8")
                            break

                        if response.status >= 400:
                            if response.status == 429:
                                yield _sse_line({
                                    "type": "error",
                                    "errorText": "Rate limit exceeded (429). Please wait a minute and try again.",
                                }).encode("utf-8")
                            else:
                                error_detail = ""
                                try:
                                    error_obj = json.loads(response_text)
                                    if isinstance(error_obj, dict):
                                        error = error_obj.get("error", {})
                                        if isinstance(error, dict):
                                            error_detail = error.get("message", "")
                                except json.JSONDecodeError:
                                    pass
                                message = error_detail or response_text or "Unknown provider error"
                                yield _sse_line({
                                    "type": "error",
                                    "errorText": f"Anthropic API error ({response.status}): {message}",
                                }).encode("utf-8")
                            break
                        # Success — process response content
                        api_data = json.loads(response_text)
                        break  # exit retry loop

            # Process successful response (if any)
            if api_data is not None:
                blocks = api_data.get("content", [])
                stop_reason = api_data.get("stop_reason")
                if stop_reason == "tool_use":
                    ai_finish = "tool-calls"
                elif stop_reason == "max_tokens":
                    ai_finish = "length"

                for block in blocks:
                    if not isinstance(block, dict):
                        continue
                    block_type = block.get("type")
                    if block_type == "text":
                        text = block.get("text", "")
                        if not text:
                            continue
                        if not text_start_emitted:
                            yield _sse_line({
                                "type": "text-start",
                                "id": text_id
                            }).encode("utf-8")
                            text_start_emitted = True
                        yield _sse_line({
                            "type": "text-delta",
                            "id": text_id,
                            "delta": text
                        }).encode("utf-8")
                        text_sent = True
                        response_text_parts.append(text)

                    if block_type == "tool_use":
                        tool_call_id = block.get("id", "")
                        tool_name = block.get("name", "")
                        tool_input = block.get("input", {})
                        if tool_call_id and tool_name:
                            call_payload = {
                                "name": tool_name,
                                "input": tool_input,
                            }
                            response_tool_calls.append(call_payload)
                            pending_tool_calls.append({
                                "toolCallId": tool_call_id,
                                "toolName": tool_name,
                                "input": tool_input if isinstance(tool_input, dict) else {}
                            })
                usage = api_data.get("usage") or {}
                in_tok = usage.get("input_tokens") or request_tokens_est
                out_tok = usage.get("output_tokens")
                if out_tok is None:
                    out_tok = _estimate_tokens("".join(response_text_parts))
                logger.info(
                    "[ComfyAssistant] tokens in=%s out=%s provider=anthropic",
                    in_tok,
                    out_tok,
                )
        except Exception as e:
            logger.debug("Anthropic request failed: %s", e, exc_info=True)
            yield _sse_line({"type": "error", "errorText": str(e)}).encode("utf-8")

        if text_sent and text_id and not text_end_sent:
            yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
            text_end_sent = True
        for tool_call in pending_tool_calls:
            yield _sse_line({
                "type": "tool-input-available",
                "toolCallId": tool_call["toolCallId"],
                "toolName": tool_call["toolName"],
                "input": tool_call["input"],
            }).encode("utf-8")
        yield _sse_line({"type": "finish", "finishReason": ai_finish}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")

    async def stream_claude_code():
        text_id = f"msg_{uuid.uuid4().hex[:24]}"
        yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

        prompt = _build_cli_tool_prompt(openai_messages)
        schema_json = json.dumps(_cli_response_schema(), ensure_ascii=False)
        cmd = [CLAUDE_CODE_COMMAND, "-p", prompt]
        if CLAUDE_CODE_MODEL:
            cmd.extend(["--model", CLAUDE_CODE_MODEL])
        cmd.extend(["--output-format", "json", "--json-schema", schema_json])

        rc, stdout, stderr, timed_out = await _run_cli_command(
            cmd,
            CLI_PROVIDER_TIMEOUT_SECONDS,
        )
        if timed_out:
            yield _sse_line({
                "type": "error",
                "errorText": stderr,
            }).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")
            return

        if rc != 0:
            message = stderr.strip() or stdout.strip() or f"{CLAUDE_CODE_COMMAND} exited with code {rc}"
            yield _sse_line({"type": "error", "errorText": message}).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")
            return

        text, tool_calls = _normalize_cli_structured_response(stdout)
        # Token count: claude_code envelope may include usage
        parsed_env = _extract_json_from_text(stdout)
        in_tok = request_tokens_est
        out_tok = None
        if isinstance(parsed_env, dict):
            usage = parsed_env.get("usage") or {}
            if usage.get("input_tokens") is not None:
                in_tok = usage["input_tokens"]
            if usage.get("output_tokens") is not None:
                out_tok = usage["output_tokens"]
        if out_tok is None:
            out_tok = _estimate_tokens(text)
        logger.info(
            "[ComfyAssistant] tokens in=%s out=%s provider=claude_code",
            in_tok,
            out_tok,
        )
        if text:
            yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
            yield _sse_line({
                "type": "text-delta",
                "id": text_id,
                "delta": text,
            }).encode("utf-8")
            yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
        for tool_call in tool_calls:
            yield _sse_line({
                "type": "tool-input-available",
                "toolCallId": f"call_{uuid.uuid4().hex[:12]}",
                "toolName": tool_call["name"],
                "input": tool_call["input"],
            }).encode("utf-8")
        finish_reason = "tool-calls" if tool_calls else "stop"
        yield _sse_line({"type": "finish", "finishReason": finish_reason}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")

    async def stream_codex():
        text_id = f"msg_{uuid.uuid4().hex[:24]}"
        yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

        prompt = _build_cli_tool_prompt(openai_messages)
        with tempfile.NamedTemporaryFile(prefix="codex-last-", suffix=".txt", delete=True) as tmp, tempfile.NamedTemporaryFile(prefix="codex-schema-", suffix=".json", mode="w", encoding="utf-8", delete=True) as schema_file:
            json.dump(_cli_response_schema(), schema_file, ensure_ascii=False)
            schema_file.flush()
            cmd = [
                CODEX_COMMAND,
                "exec",
                "--skip-git-repo-check",
                "--color",
                "never",
                "--output-schema",
                schema_file.name,
                "-o",
                tmp.name,
                prompt,
            ]
            if CODEX_MODEL:
                cmd.extend(["--model", CODEX_MODEL])

            rc, stdout, stderr, timed_out = await _run_cli_command(
                cmd,
                CLI_PROVIDER_TIMEOUT_SECONDS,
            )
            if timed_out:
                yield _sse_line({
                    "type": "error",
                    "errorText": stderr,
                }).encode("utf-8")
                yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
                yield "data: [DONE]\n\n".encode("utf-8")
                return

            if rc != 0:
                message = stderr.strip() or stdout.strip() or f"{CODEX_COMMAND} exited with code {rc}"
                yield _sse_line({"type": "error", "errorText": message}).encode("utf-8")
                yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
                yield "data: [DONE]\n\n".encode("utf-8")
                return

            last_message = ""
            try:
                with open(tmp.name, "r", encoding="utf-8") as f:
                    last_message = f.read().strip()
            except Exception:
                last_message = ""
            raw = last_message or stdout.strip()
            text, tool_calls = _normalize_cli_structured_response(raw)
            in_tok = request_tokens_est
            out_tok = _estimate_tokens(text)
            logger.info(
                "[ComfyAssistant] tokens in=%s out=%s provider=codex",
                in_tok,
                out_tok,
            )
            if text:
                yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                yield _sse_line({
                    "type": "text-delta",
                    "id": text_id,
                    "delta": text,
                }).encode("utf-8")
                yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
            for tool_call in tool_calls:
                yield _sse_line({
                    "type": "tool-input-available",
                    "toolCallId": f"call_{uuid.uuid4().hex[:12]}",
                    "toolName": tool_call["name"],
                    "input": tool_call["input"],
                }).encode("utf-8")
            finish_reason = "tool-calls" if tool_calls else "stop"
        yield _sse_line({"type": "finish", "finishReason": finish_reason}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")

    async def stream_gemini_cli():
        text_id = f"msg_{uuid.uuid4().hex[:24]}"
        yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

        prompt = _build_cli_tool_prompt(openai_messages)
        # Gemini CLI does not support --json-schema; embed schema in prompt text
        schema_json = json.dumps(_cli_response_schema(), ensure_ascii=False)
        full_prompt = (
            prompt
            + "\n\nIMPORTANT: You MUST respond with a single JSON object matching this schema:\n"
            + schema_json
        )
        cmd = [GEMINI_CLI_COMMAND, "-p", full_prompt, "--output-format", "json"]
        if GEMINI_CLI_MODEL:
            cmd.extend(["-m", GEMINI_CLI_MODEL])

        rc, stdout, stderr, timed_out = await _run_cli_command(
            cmd,
            CLI_PROVIDER_TIMEOUT_SECONDS,
        )
        if timed_out:
            yield _sse_line({
                "type": "error",
                "errorText": stderr,
            }).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")
            return

        if rc != 0:
            message = stderr.strip() or stdout.strip() or f"{GEMINI_CLI_COMMAND} exited with code {rc}"
            yield _sse_line({"type": "error", "errorText": message}).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")
            return

        # Gemini CLI JSON envelope: {"response": "...", "stats": {...}, "error": {...}}
        # Unwrap the envelope before normalizing.
        raw = stdout.strip()
        in_tok = request_tokens_est
        out_tok = None
        gemini_env = _extract_json_from_text(raw)
        if isinstance(gemini_env, dict) and "response" in gemini_env:
            # Extract token stats from Gemini envelope
            stats = gemini_env.get("stats")
            if isinstance(stats, dict):
                if stats.get("inputTokens") is not None:
                    in_tok = stats["inputTokens"]
                elif stats.get("input_tokens") is not None:
                    in_tok = stats["input_tokens"]
                if stats.get("outputTokens") is not None:
                    out_tok = stats["outputTokens"]
                elif stats.get("output_tokens") is not None:
                    out_tok = stats["output_tokens"]
            # Check for Gemini-level error
            gemini_error = gemini_env.get("error")
            if isinstance(gemini_error, dict) and gemini_error.get("message"):
                yield _sse_line({
                    "type": "error",
                    "errorText": gemini_error["message"],
                }).encode("utf-8")
                yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
                yield "data: [DONE]\n\n".encode("utf-8")
                return
            raw = gemini_env["response"] if isinstance(gemini_env["response"], str) else json.dumps(gemini_env["response"])

        text, tool_calls = _normalize_cli_structured_response(raw)
        if out_tok is None:
            out_tok = _estimate_tokens(text)
        logger.info(
            "[ComfyAssistant] tokens in=%s out=%s provider=gemini_cli",
            in_tok,
            out_tok,
        )
        if text:
            yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
            yield _sse_line({
                "type": "text-delta",
                "id": text_id,
                "delta": text,
            }).encode("utf-8")
            yield _sse_line({"type": "text-end", "id": text_id}).encode("utf-8")
        for tool_call in tool_calls:
            yield _sse_line({
                "type": "tool-input-available",
                "toolCallId": f"call_{uuid.uuid4().hex[:12]}",
                "toolName": tool_call["name"],
                "input": tool_call["input"],
            }).encode("utf-8")
        finish_reason = "tool-calls" if tool_calls else "stop"
        yield _sse_line({"type": "finish", "finishReason": finish_reason}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")

    if selected_provider == "openai":
        stream_fn = stream_openai
    elif selected_provider == "anthropic":
        stream_fn = stream_anthropic
    elif selected_provider == "claude_code":
        stream_fn = stream_claude_code
    elif selected_provider == "gemini_cli":
        stream_fn = stream_gemini_cli
    else:
        stream_fn = stream_codex

    async def stream_with_logging():
        if not COMFY_ASSISTANT_ENABLE_LOGS:
            async for chunk in stream_fn():
                yield chunk
            return

        response_text_parts = []
        response_tool_calls = []
        thread_id = "default"
        # Try to find thread_id from last message
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("id"):
                thread_id = msg.get("id")
                break

        async for chunk in stream_fn():
            yield chunk
            
            # Intercept and accumulate for logging
            try:
                line = chunk.decode("utf-8")
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "text-delta":
                        response_text_parts.append(data.get("delta", ""))
                    elif data.get("type") == "tool-input-available":
                        response_tool_calls.append({
                            "name": data.get("toolName"),
                            "input": data.get("input")
                        })
            except Exception:
                pass

        # At the end of the stream, write the log
        try:
            full_assistant_reply = "".join(response_text_parts)
            conversation_logger.log_interaction(
                thread_id=thread_id,
                user_message=last_user_text,
                assistant_response=full_assistant_reply,
                tool_calls=response_tool_calls
            )
        except Exception as log_err:
            logger.error("[ComfyAssistant] Failed to log interaction: %s", log_err)

    resp = web.StreamResponse(status=200, headers=response_headers)
    await resp.prepare(request)
    first_chunk = True
    async for chunk in stream_with_logging():
        await resp.write(chunk)
        # Emit debug SSE event right after the first event (start)
        if first_chunk and debug_context:
            first_chunk = False
            debug_event = _sse_line({
                "type": "context-debug",
                "metrics": metrics,
            })
            await resp.write(debug_event.encode("utf-8"))
    return resp


async def user_context_status_handler(request: web.Request) -> web.Response:
    """GET /api/user-context/status. Returns { needsOnboarding: true } if onboarding not done."""
    try:
        needs = not user_context_store.get_onboarding_done()
        return web.json_response({"needsOnboarding": needs})
    except Exception:
        return web.json_response({"needsOnboarding": True}, status=200)


async def user_context_onboarding_handler(request: web.Request) -> web.Response:
    """POST /api/user-context/onboarding. Body: { personality?, goals?, experienceLevel? } or skip."""
    try:
        body = await request.json() if request.body_exists else {}
    except json.JSONDecodeError:
        body = {}
    try:
        skip = body.get("skip", False)
        if skip:
            user_context_store.save_onboarding("", "", "")
            return web.json_response({"ok": True})
        personality = body.get("personality", "") or ""
        goals = body.get("goals", "") or ""
        experience_level = body.get("experienceLevel", "") or ""
        user_context_store.save_onboarding(
            personality=personality,
            goals=goals,
            experience_level=experience_level,
        )
        return web.json_response({"ok": True})
    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


# --- Environment & Skill API handlers (extracted to api_handlers.py) ---

environment_dir = os.path.join(user_context_path, "environment")

_phase3_handlers = api_handlers.create_handlers(
    environment_dir=environment_dir,
    system_context_path=system_context_path,
)

# Register the chat API route (must be registered before static routes so /api/chat is handled)
server.PromptServer.instance.app.add_routes([
    web.post("/api/chat", chat_api_handler),
    web.get("/api/user-context/status", user_context_status_handler),
    web.post("/api/user-context/onboarding", user_context_onboarding_handler),
])
# Register Phase 3 routes (environment, docs, skills)
api_handlers.register_routes(server.PromptServer.instance.app, _phase3_handlers)

# Register Phase 8 routes (research: web search, content fetch, node registry)
_phase8_handlers = api_handlers.create_research_handlers()
api_handlers.register_research_routes(server.PromptServer.instance.app, _phase8_handlers)


# --- Auto-scan environment on startup (non-blocking) ---

async def _auto_scan_environment():
    """Run initial environment scan after a delay to let other custom nodes finish loading."""
    await asyncio.sleep(5)  # Wait for other extensions to register
    try:
        user_context_store.ensure_environment_dirs()
        summary = environment_scanner.scan_environment(environment_dir)
        logger.info(
            "Auto-scan complete: %d node types, %d packages, %d models",
            summary.get("node_types_count", 0),
            summary.get("custom_packages_count", 0),
            summary.get("models_count", 0),
        )
    except Exception as e:
        logger.warning("Auto-scan failed (non-critical): %s", e)

# Schedule auto-scan as a background task
try:
    loop = asyncio.get_event_loop()
    loop.create_task(_auto_scan_environment())
except RuntimeError:
    # No event loop available yet; skip auto-scan
    pass

# Register the static route for serving our React app assets
if os.path.exists(dist_path):
    # Add the routes for the extension
    server.PromptServer.instance.app.add_routes([
        web.static("/example_ext/", dist_path),
    ])

    # Register the locale files route
    if os.path.exists(dist_locales_path):
        server.PromptServer.instance.app.add_routes([
            web.static("/locales/", dist_locales_path),
        ])
        print(f"Registered locale files route at /locales/")
    else:
        print("WARNING: Locale directory not found!")

    # Also register the standard ComfyUI extension web directory

    project_name = os.path.basename(workspace_path)

    try:
        # Method added in https://github.com/comfyanonymous/ComfyUI/pull/8357
        from comfy_config import config_parser

        project_config = config_parser.extract_node_configuration(workspace_path)
        project_name = project_config.project.name
        print(f"project name read from pyproject.toml: {project_name}")
    except Exception as e:
        print(f"Could not load project config, using default name '{project_name}': {e}")

    nodes.EXTENSION_WEB_DIRS[project_name] = os.path.join(workspace_path, "dist")
else:
    print("ComfyUI Example React Extension: Web directory not found")
