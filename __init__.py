import asyncio
import os
import json
import logging
import uuid
from collections.abc import AsyncGenerator
import server
from aiohttp import web
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
import provider_manager
import provider_store
from cli_providers import _has_cli_provider_command
from tools_definitions import TOOLS
from message_transforms import (
    _extract_content,
    _ui_messages_to_openai,
)
from context_management import (
    LLM_HISTORY_MAX_MESSAGES,
    LLM_SYSTEM_CONTEXT_MAX_CHARS,
    LLM_TOOL_RESULT_KEEP_LAST_ROUNDS,
    LLM_USER_CONTEXT_MAX_CHARS,
    _build_conversation_summary,
    _build_tool_name_map,
    _count_request_tokens,
    _estimate_tokens,
    _format_context_log_summary,
    _smart_truncate_system_context,
    _trim_old_tool_results,
    _trim_openai_history,
)
from provider_streaming import (
    stream_anthropic,
    stream_claude_code,
    stream_codex,
    stream_gemini_cli,
    stream_openai,
)
from sse_streaming import (
    UI_MESSAGE_STREAM_HEADERS,
    _sse_line,
    _stream_ai_sdk_text,
)
from slash_commands import (
    _format_provider_line,
    _handle_provider_command,
    _inject_skill_if_slash_skill,
    _resolve_skill_by_name_or_slug,
)
from chat_utilities import (
    _get_last_openai_user_text,
    _get_last_user_text,
    _is_context_too_large_error,
    _is_context_too_large_response,
    _openai_message_content_to_str,
    _set_openai_message_content,
)


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
provider_store.init_providers_db()
provider_manager.reload_provider()

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


# Enable conversation logging in user_context/logs/
COMFY_ASSISTANT_ENABLE_LOGS = os.environ.get(
    "COMFY_ASSISTANT_ENABLE_LOGS", ""
).strip().lower() in ("1", "true", "yes")

# Debug: emit context-pipeline metrics in logs, headers, and SSE events.
# Enabled per-request via ?debug=context or always-on via this env var.
COMFY_ASSISTANT_DEBUG_CONTEXT = os.environ.get(
    "COMFY_ASSISTANT_DEBUG_CONTEXT", ""
).strip().lower() in ("1", "true", "yes")
LLM_VERBOSE_LOGGING = os.environ.get(
    "LLM_VERBOSE_LOGGING", ""
).strip().lower() in ("1", "true", "yes")

# Maximum automatic compaction retries when the LLM returns 413 / context-too-large.
_MAX_CONTEXT_COMPACT_RETRIES = 2

# Tools definitions: imported from tools_definitions.py (single source of truth)
TOOLS_DEFINITIONS = TOOLS


def _has_anthropic_credentials(api_key: str | None = None) -> bool:
    """Return True when Anthropic API key auth is available."""
    if api_key is not None:
        return bool(api_key)
    return bool(ANTHROPIC_API_KEY)


def _selected_llm_provider() -> str:
    """Resolve active provider from env and available credentials."""
    active = provider_store.get_active_provider()
    if active and active.get("provider_type") in {"openai", "anthropic", "claude_code", "codex", "gemini_cli"}:
        return active["provider_type"]
    if LLM_PROVIDER in {"openai", "anthropic", "claude_code", "codex", "gemini_cli"}:
        return LLM_PROVIDER
    if OPENAI_API_KEY:
        return "openai"
    if _has_anthropic_credentials():
        return "anthropic"
    return "openai"


# Print the current paths for debugging
print(f"ComfyUI_example_frontend_extension workspace path: {workspace_path}")
print(f"Dist path: {dist_path}")
print(f"Dist locales path: {dist_locales_path}")
print(f"Locales exist: {os.path.exists(dist_locales_path)}")



async def _create_empty_stream_response(
    request: web.Request,
    message_id: str | None = None,
) -> web.Response:
    """Return an empty SSE stream (start/finish/DONE)."""
    stream_message_id = message_id or f"msg_{uuid.uuid4().hex}"

    async def stream_empty():
        yield _sse_line({"type": "start", "messageId": stream_message_id}).encode("utf-8")
        yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
        yield "data: [DONE]\n\n".encode("utf-8")

    resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
    await resp.prepare(request)
    async for chunk in stream_empty():
        await resp.write(chunk)
    return resp


async def _prepare_chat_request(request: web.Request) -> tuple[list[dict], dict]:
    """Parse request payload and return OpenAI-style messages plus metrics state."""
    try:
        body = await request.json() if request.body_exists else {}
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON body")

    messages = body.get("messages", [])
    metrics: dict = {
        "_raw_messages": messages,
        "_message_id": f"msg_{uuid.uuid4().hex}",
        "_debug_context": COMFY_ASSISTANT_DEBUG_CONTEXT or (
            request.query.get("debug") == "context"
        ),
    }

    raw_last_user = _get_last_user_text(messages).strip()
    metrics["_raw_last_user"] = raw_last_user
    metrics["_raw_last_user_lower"] = raw_last_user.lower()

    if messages:
        last_msg = messages[-1]
        if isinstance(last_msg, dict) and last_msg.get("role") == "assistant":
            content = _extract_content(last_msg)
            if isinstance(content, str) and "<!-- local:slash -->" in content:
                metrics["_local_empty_stream"] = True
                return ([], metrics)

    openai_messages = _ui_messages_to_openai(messages)

    logger.info("[DEBUG] Input messages count: %d", len(messages))
    logger.info("[DEBUG] Converted openai_messages count: %d", len(openai_messages))
    for i, msg in enumerate(openai_messages):
        logger.info(
            "[DEBUG] Message %d: role=%s content=%s",
            i,
            msg.get("role"),
            str(msg.get("content", ""))[:100],
        )

    return (openai_messages, metrics)


def _build_system_message_block(openai_messages: list[dict], metrics: dict) -> None:
    """Inject system block when missing, using full context only on first turn."""
    importlib.reload(agent_prompts)
    from agent_prompts import get_system_message, get_system_message_continuation
    import user_context_loader

    has_system = any(msg.get("role") == "system" for msg in openai_messages)
    has_prior_assistant = any(msg.get("role") == "assistant" for msg in openai_messages)
    metrics["is_first_turn"] = not has_prior_assistant

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
            openai_messages.insert(
                0,
                get_system_message_continuation(
                    user_skills=user_skills_list,
                    environment_summary=environment_summary,
                ),
            )
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


def _apply_context_pipeline(openai_messages: list[dict], metrics: dict) -> list[dict]:
    """Apply slash-skill injection and context trimming pipeline."""
    _inject_skill_if_slash_skill(openai_messages)
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
    return openai_messages


def _select_provider_and_stream(
    openai_messages: list[dict],
    metrics: dict,
) -> AsyncGenerator[bytes, None]:
    """Resolve provider config and return the selected stream generator."""
    message_id = str(metrics.get("_message_id") or f"msg_{uuid.uuid4().hex}")
    runtime_provider = provider_manager.get_current_provider_config()
    selected_provider = str(
        runtime_provider.get("provider_type") or _selected_llm_provider()
    )

    openai_api_key = OPENAI_API_KEY
    openai_model = OPENAI_MODEL
    openai_base_url = OPENAI_API_BASE_URL

    anthropic_api_key = ANTHROPIC_API_KEY
    anthropic_model = ANTHROPIC_MODEL
    anthropic_base_url = ANTHROPIC_BASE_URL
    anthropic_max_tokens = ANTHROPIC_MAX_TOKENS

    claude_code_command = CLAUDE_CODE_COMMAND
    claude_code_model = CLAUDE_CODE_MODEL
    codex_command = CODEX_COMMAND
    codex_model = CODEX_MODEL
    gemini_cli_command = GEMINI_CLI_COMMAND
    gemini_cli_model = GEMINI_CLI_MODEL
    cli_provider_timeout_seconds = CLI_PROVIDER_TIMEOUT_SECONDS

    if selected_provider == "openai":
        openai_api_key = str(runtime_provider.get("api_key") or "")
        openai_model = str(runtime_provider.get("model") or OPENAI_MODEL or "gpt-4o")
        openai_base_url = str(
            runtime_provider.get("base_url") or OPENAI_API_BASE_URL
        ).rstrip("/")
    elif selected_provider == "anthropic":
        anthropic_api_key = str(runtime_provider.get("api_key") or "")
        anthropic_model = str(
            runtime_provider.get("model") or ANTHROPIC_MODEL or "claude-sonnet-4-5"
        )
        anthropic_base_url = str(
            runtime_provider.get("base_url") or ANTHROPIC_BASE_URL
        ).rstrip("/")
        try:
            anthropic_max_tokens = int(
                runtime_provider.get("max_tokens") or ANTHROPIC_MAX_TOKENS
            )
        except (TypeError, ValueError):
            anthropic_max_tokens = ANTHROPIC_MAX_TOKENS
    elif selected_provider == "claude_code":
        claude_code_command = str(runtime_provider.get("cli_command") or CLAUDE_CODE_COMMAND)
        claude_code_model = str(runtime_provider.get("cli_model") or CLAUDE_CODE_MODEL)
        try:
            cli_provider_timeout_seconds = int(
                runtime_provider.get("timeout_seconds") or CLI_PROVIDER_TIMEOUT_SECONDS
            )
        except (TypeError, ValueError):
            cli_provider_timeout_seconds = CLI_PROVIDER_TIMEOUT_SECONDS
    elif selected_provider == "codex":
        codex_command = str(runtime_provider.get("cli_command") or CODEX_COMMAND)
        codex_model = str(runtime_provider.get("cli_model") or CODEX_MODEL)
        try:
            cli_provider_timeout_seconds = int(
                runtime_provider.get("timeout_seconds") or CLI_PROVIDER_TIMEOUT_SECONDS
            )
        except (TypeError, ValueError):
            cli_provider_timeout_seconds = CLI_PROVIDER_TIMEOUT_SECONDS
    elif selected_provider == "gemini_cli":
        gemini_cli_command = str(runtime_provider.get("cli_command") or GEMINI_CLI_COMMAND)
        gemini_cli_model = str(runtime_provider.get("cli_model") or GEMINI_CLI_MODEL)
        try:
            cli_provider_timeout_seconds = int(
                runtime_provider.get("timeout_seconds") or CLI_PROVIDER_TIMEOUT_SECONDS
            )
        except (TypeError, ValueError):
            cli_provider_timeout_seconds = CLI_PROVIDER_TIMEOUT_SECONDS

    raw_last_user = str(metrics.get("_raw_last_user", "")).strip()
    raw_last_user_lower = str(metrics.get("_raw_last_user_lower", "")).strip()
    if raw_last_user_lower.startswith("/provider"):
        command_result = _handle_provider_command(raw_last_user)

        async def stream_local_command():
            for chunk in _stream_ai_sdk_text(command_result.get("text", ""), message_id):
                yield chunk.encode("utf-8")

        return stream_local_command()

    if selected_provider == "claude_code":
        placeholder = (
            f"Chat API is not configured. Install `{claude_code_command}` "
            "or set CLI command in provider settings."
        )
        has_provider_credentials = _has_cli_provider_command(
            "claude_code", command=claude_code_command
        )
    elif selected_provider == "codex":
        placeholder = (
            f"Chat API is not configured. Install `{codex_command}` "
            "or set CLI command in provider settings."
        )
        has_provider_credentials = _has_cli_provider_command(
            "codex", command=codex_command
        )
    elif selected_provider == "gemini_cli":
        placeholder = (
            f"Chat API is not configured. Install `{gemini_cli_command}` "
            "or set CLI command in provider settings."
        )
        has_provider_credentials = _has_cli_provider_command(
            "gemini_cli", command=gemini_cli_command
        )
    elif selected_provider == "anthropic":
        placeholder = (
            "Chat API is not configured. Set an Anthropic API key in provider settings."
        )
        has_provider_credentials = _has_anthropic_credentials(anthropic_api_key)
    else:
        placeholder = (
            "Chat API is not configured. Set an OpenAI API key in provider settings."
        )
        has_provider_credentials = bool(openai_api_key)

    if not has_provider_credentials:
        async def stream_placeholder():
            for chunk in _stream_ai_sdk_text(placeholder, message_id):
                yield chunk.encode("utf-8")

        return stream_placeholder()

    if raw_last_user.startswith("/") and not (
        raw_last_user_lower.startswith("/skill")
        or raw_last_user_lower.startswith("/provider")
    ):
        async def stream_empty():
            yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")

        return stream_empty()

    last_user_text = _get_last_openai_user_text(openai_messages).strip()
    metrics["_last_user_text"] = last_user_text
    if not last_user_text:
        async def stream_empty():
            yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")
            yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
            yield "data: [DONE]\n\n".encode("utf-8")

        return stream_empty()

    request_tokens_est = _count_request_tokens(openai_messages)
    total_chars = sum(
        len(m.get("content", "")) if isinstance(m.get("content"), str) else 0
        for m in openai_messages
    )
    metrics["total_messages"] = len(openai_messages)
    metrics["total_chars"] = total_chars
    metrics["total_tokens_est"] = request_tokens_est
    metrics["total_tokens_quick_est"] = _estimate_tokens("x" * total_chars) if total_chars else 0
    metrics["provider"] = selected_provider
    logger.info(
        "[ComfyAssistant] context: %s",
        _format_context_log_summary(metrics),
    )
    logger.debug(
        "[ComfyAssistant] context metrics: %s",
        json.dumps(metrics, default=str),
    )

    if selected_provider == "openai":
        async def stream_fn():
            async for chunk in stream_openai(
                message_id=message_id,
                openai_messages=openai_messages,
                openai_api_key=openai_api_key,
                openai_base_url=openai_base_url,
                openai_model=openai_model,
                llm_request_delay_seconds=LLM_REQUEST_DELAY_SECONDS,
                max_context_compact_retries=_MAX_CONTEXT_COMPACT_RETRIES,
                request_tokens_est=request_tokens_est,
                logger=logger,
                is_context_too_large_error=_is_context_too_large_error,
                count_request_tokens=_count_request_tokens,
                tools_definitions=TOOLS_DEFINITIONS,
            ):
                yield chunk
    elif selected_provider == "anthropic":
        async def stream_fn():
            async for chunk in stream_anthropic(
                message_id=message_id,
                openai_messages=openai_messages,
                anthropic_api_key=anthropic_api_key,
                anthropic_model=anthropic_model,
                anthropic_max_tokens=anthropic_max_tokens,
                anthropic_base_url=anthropic_base_url,
                llm_request_delay_seconds=LLM_REQUEST_DELAY_SECONDS,
                max_context_compact_retries=_MAX_CONTEXT_COMPACT_RETRIES,
                request_tokens_est=request_tokens_est,
                logger=logger,
                is_context_too_large_response=_is_context_too_large_response,
                count_request_tokens=_count_request_tokens,
                tools_definitions=TOOLS_DEFINITIONS,
            ):
                yield chunk
    elif selected_provider == "claude_code":
        async def stream_fn():
            async for chunk in stream_claude_code(
                message_id=message_id,
                openai_messages=openai_messages,
                claude_code_command=claude_code_command,
                claude_code_model=claude_code_model,
                cli_provider_timeout_seconds=cli_provider_timeout_seconds,
                request_tokens_est=request_tokens_est,
                logger=logger,
            ):
                yield chunk
    elif selected_provider == "gemini_cli":
        async def stream_fn():
            async for chunk in stream_gemini_cli(
                message_id=message_id,
                openai_messages=openai_messages,
                gemini_cli_command=gemini_cli_command,
                gemini_cli_model=gemini_cli_model,
                cli_provider_timeout_seconds=cli_provider_timeout_seconds,
                request_tokens_est=request_tokens_est,
                logger=logger,
            ):
                yield chunk
    else:
        async def stream_fn():
            async for chunk in stream_codex(
                message_id=message_id,
                openai_messages=openai_messages,
                codex_command=codex_command,
                codex_model=codex_model,
                cli_provider_timeout_seconds=cli_provider_timeout_seconds,
                request_tokens_est=request_tokens_est,
                logger=logger,
            ):
                yield chunk

    return stream_fn()


async def _create_streaming_response(
    stream_gen: AsyncGenerator[bytes, None],
    request: web.Request,
    metrics: dict,
) -> web.Response:
    """Build StreamResponse, wrap stream with logging, and emit debug metadata."""
    debug_context = bool(metrics.get("_debug_context"))
    header_debug_enabled = debug_context or LLM_VERBOSE_LOGGING
    raw_messages = metrics.get("_raw_messages") or []
    last_user_text = str(metrics.get("_last_user_text") or "")

    if header_debug_enabled:
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

    async def stream_with_logging():
        if not COMFY_ASSISTANT_ENABLE_LOGS:
            async for chunk in stream_gen:
                yield chunk
            return

        response_text_parts = []
        response_tool_calls = []
        thread_id = "default"
        for msg in reversed(raw_messages):
            if isinstance(msg, dict) and msg.get("id"):
                thread_id = msg.get("id")
                break

        async for chunk in stream_gen:
            yield chunk

            try:
                line = chunk.decode("utf-8")
                if line.startswith("data: "):
                    data = json.loads(line[6:])
                    if data.get("type") == "text-delta":
                        response_text_parts.append(data.get("delta", ""))
                    elif data.get("type") == "tool-input-available":
                        response_tool_calls.append({
                            "name": data.get("toolName"),
                            "input": data.get("input"),
                        })
            except Exception:
                pass

        try:
            full_assistant_reply = "".join(response_text_parts)
            conversation_logger.log_interaction(
                thread_id=thread_id,
                user_message=last_user_text,
                assistant_response=full_assistant_reply,
                tool_calls=response_tool_calls,
            )
        except Exception as log_err:
            logger.error("[ComfyAssistant] Failed to log interaction: %s", log_err)

    resp = web.StreamResponse(status=200, headers=response_headers)
    await resp.prepare(request)
    first_chunk = True
    async for chunk in stream_with_logging():
        await resp.write(chunk)
        if first_chunk and debug_context:
            first_chunk = False
            debug_event = _sse_line({
                "type": "context-debug",
                "metrics": metrics,
            })
            await resp.write(debug_event.encode("utf-8"))
    return resp


async def chat_api_handler(request: web.Request) -> web.Response:
    """Handle POST /api/chat with AI streaming."""
    try:
        openai_messages, metrics = await _prepare_chat_request(request)
    except ValueError:
        return web.json_response(
            {"error": "Invalid JSON body"},
            status=400,
        )

    if metrics.get("_local_empty_stream"):
        return await _create_empty_stream_response(
            request,
            message_id=str(metrics.get("_message_id") or ""),
        )

    _build_system_message_block(openai_messages, metrics)
    openai_messages = _apply_context_pipeline(openai_messages, metrics)

    stream_gen = _select_provider_and_stream(openai_messages, metrics)

    return await _create_streaming_response(stream_gen, request, metrics)


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
_provider_handlers = api_handlers.create_provider_handlers()

# Register the chat API route (must be registered before static routes so /api/chat is handled)
server.PromptServer.instance.app.add_routes([
    web.post("/api/chat", chat_api_handler),
    web.get("/api/user-context/status", user_context_status_handler),
    web.post("/api/user-context/onboarding", user_context_onboarding_handler),
])
# Register Phase 3 routes (environment, docs, skills)
api_handlers.register_routes(server.PromptServer.instance.app, _phase3_handlers)
# Register provider wizard routes
api_handlers.register_provider_routes(server.PromptServer.instance.app, _provider_handlers)

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
