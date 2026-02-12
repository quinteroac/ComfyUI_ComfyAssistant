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
    command = CLAUDE_CODE_COMMAND if provider == "claude_code" else CODEX_COMMAND
    return bool(command) and shutil.which(command) is not None


def _selected_llm_provider() -> str:
    """Resolve active provider from env and available credentials."""
    if LLM_PROVIDER in {"openai", "anthropic", "claude_code", "codex"}:
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
            openai_msg = {"role": "assistant"}

            # Extract text content
            content = _extract_content(msg)
            if content:
                openai_msg["content"] = content

            # Extract tool calls and results from parts (deduplicate by id so
            # we never send duplicate tool_calls/tool_results to the LLM)
            tool_calls = []
            tool_calls_seen: set[str] = set()
            tool_results = []
            tool_results_seen: set[str] = set()
            parts = msg.get("parts", [])

            for part in parts:
                if not isinstance(part, dict):
                    continue

                part_type = part.get("type", "")

                # AI SDK v6 format: type starts with 'tool-' or is 'dynamic-tool'
                if _is_tool_ui_part(part):
                    tool_name = _get_tool_name(part)
                    tool_call_id = part.get("toolCallId", "")
                    state = part.get("state", "")
                    args = part.get("input", {})

                    # Add tool call only once per id
                    if tool_call_id and tool_call_id not in tool_calls_seen:
                        tool_calls_seen.add(tool_call_id)
                        tool_calls.append({
                            "id": tool_call_id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": json.dumps(args) if args else "{}"
                            }
                        })

                    # If the tool has completed, add a tool result message (once per id)
                    if state == "output-available" and "output" in part:
                        if tool_call_id and tool_call_id not in tool_results_seen:
                            tool_results_seen.add(tool_call_id)
                            tool_results.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps(part.get("output", {}))
                            })
                    elif state == "output-error":
                        if tool_call_id and tool_call_id not in tool_results_seen:
                            tool_results_seen.add(tool_call_id)
                            tool_results.append({
                                "role": "tool",
                                "tool_call_id": tool_call_id,
                                "content": json.dumps({
                                    "error": part.get("errorText", "Unknown error")
                                })
                            })

                # Legacy format: type == 'tool-call'
                elif part_type == "tool-call":
                    tid = part.get("toolCallId", "")
                    if tid and tid not in tool_calls_seen:
                        tool_calls_seen.add(tid)
                        tool_calls.append({
                            "id": tid,
                            "type": "function",
                            "function": {
                                "name": part.get("toolName", ""),
                                "arguments": json.dumps(part.get("args", {}))
                            }
                        })

            if tool_calls:
                openai_msg["tool_calls"] = tool_calls

            # Only add message if it has content or tool_calls
            if "content" in openai_msg or "tool_calls" in openai_msg:
                result.append(openai_msg)

            # Append tool results as separate messages (OpenAI format requires
            # role='tool' messages after the assistant message with tool_calls)
            result.extend(tool_results)

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


def _truncate_chars(text: str, max_chars: int) -> str:
    """Hard-truncate text with a suffix marker."""
    if max_chars <= 0:
        return ""
    if len(text) <= max_chars:
        return text
    suffix = "... [truncated]"
    keep = max(0, max_chars - len(suffix))
    return text[:keep].rstrip() + suffix


def _estimate_tokens(text: str) -> int:
    """Rough token estimate from character count (~4 chars per token)."""
    if not text:
        return 0
    return max(1, len(text) // 4)


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


# Placeholder for tool results from older rounds (to keep API order intact but save context).
_TOOL_RESULT_OMITTED_PLACEHOLDER = '{"_omitted": true, "note": "Earlier tool result omitted to save context"}'

def _trim_old_tool_results(messages: list[dict], keep_last_n_rounds: int) -> list[dict]:
    """Replace content of tool results from older rounds with a short placeholder.
    A 'round' is one assistant message with tool_calls plus the immediately following tool messages.
    Only the last keep_last_n_rounds rounds keep full content; older tool messages get the placeholder."""
    if keep_last_n_rounds <= 0:
        # Replace all tool results
        out = []
        for m in messages:
            m = dict(m)
            if m.get("role") == "tool":
                m["content"] = _TOOL_RESULT_OMITTED_PLACEHOLDER
            out.append(m)
        return out

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
        return list(messages)

    # Keep full content only for the last keep_last_n_rounds rounds.
    rounds_to_keep = set()
    for (_, indices) in rounds[-keep_last_n_rounds:]:
        rounds_to_keep.update(indices)

    out = []
    for idx, m in enumerate(messages):
        m = dict(m)
        if m.get("role") == "tool" and idx not in rounds_to_keep:
            m["content"] = _TOOL_RESULT_OMITTED_PLACEHOLDER
        out.append(m)
    return out


def _trim_openai_history(messages: list[dict], max_non_system_messages: int) -> list[dict]:
    """Trim non-system history to a bounded tail while preserving system message(s)."""
    if max_non_system_messages <= 0:
        return [m for m in messages if m.get("role") == "system"]

    system_messages = [m for m in messages if m.get("role") == "system"]
    non_system = [m for m in messages if m.get("role") != "system"]
    if len(non_system) <= max_non_system_messages:
        return messages

    tail = non_system[-max_non_system_messages:]
    # Avoid starting with orphan tool results.
    while tail and tail[0].get("role") == "tool":
        tail = tail[1:]
    return system_messages + tail

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
    
    # Reload agent_prompts to pick up any changes (useful during development)
    importlib.reload(agent_prompts)
    from agent_prompts import get_system_message, get_system_message_continuation
    import user_context_loader

    # Add system message if not present. Send full context only on first turn to avoid
    # re-sending the same long context on every request; use short continuation otherwise.
    has_system = any(msg.get("role") == "system" for msg in openai_messages)
    has_prior_assistant = any(msg.get("role") == "assistant" for msg in openai_messages)
    if not has_system:
        if has_prior_assistant:
            openai_messages.insert(0, get_system_message_continuation())
        else:
            system_context_text = ""
            user_context = None
            environment_summary = ""
            try:
                system_context_text = user_context_loader.load_system_context(system_context_path)
                user_context = user_context_loader.load_user_context()
                environment_summary = user_context_loader.load_environment_summary()
            except Exception:
                pass
            system_context_text = _truncate_chars(
                system_context_text,
                LLM_SYSTEM_CONTEXT_MAX_CHARS
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
                ),
            )
    # Handle /skill <name>: resolve skill and inject into this turn; replace user message
    _inject_skill_if_slash_skill(openai_messages)
    # Keep full tool results only for the last N rounds; older ones get a short placeholder
    openai_messages = _trim_old_tool_results(
        openai_messages,
        LLM_TOOL_RESULT_KEEP_LAST_ROUNDS,
    )
    openai_messages = _trim_openai_history(
        openai_messages,
        LLM_HISTORY_MAX_MESSAGES,
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
    logger.info(
        "[ComfyAssistant] tokens request=%s (est) provider=%s",
        request_tokens_est,
        selected_provider,
    )

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
            stream = await client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=openai_messages,
                tools=TOOLS_DEFINITIONS,
                tool_choice="auto",
                stream=True,
            )

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
            # User-friendly message for rate limit (429); other errors pass through
            status = getattr(e, "status_code", None) or (
                getattr(getattr(e, "response", None), "status_code", None)
            )
            if status == 429:
                yield _sse_line({
                    "type": "error",
                    "errorText": "Rate limit exceeded (429). Please wait a minute and try again.",
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

        system_text, anthropic_messages = _openai_messages_to_anthropic(
            openai_messages
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

        try:
            await asyncio.sleep(LLM_REQUEST_DELAY_SECONDS)
            async with ClientSession() as session:
                async with session.post(
                    f"{ANTHROPIC_BASE_URL}/v1/messages",
                    headers=headers,
                    json=payload,
                ) as response:
                    response_text = await response.text()
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
                    else:
                        data = json.loads(response_text)
                        blocks = data.get("content", [])
                        stop_reason = data.get("stop_reason")
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
                        usage = data.get("usage") or {}
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

    if selected_provider == "openai":
        stream_fn = stream_openai
    elif selected_provider == "anthropic":
        stream_fn = stream_anthropic
    elif selected_provider == "claude_code":
        stream_fn = stream_claude_code
    else:
        stream_fn = stream_codex
    resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
    await resp.prepare(request)
    async for chunk in stream_fn():
        await resp.write(chunk)
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
