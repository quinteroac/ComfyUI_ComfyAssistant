import asyncio
import os
import json
import logging
import uuid
import re
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

# LLM config from .env (OpenAI-compatible: Groq, OpenAI, Together, Ollama, etc.)
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama3-70b-8192")
OPENAI_API_BASE_URL = os.environ.get(
    "OPENAI_API_BASE_URL",
    "https://api.groq.com/openai/v1",
).rstrip("/")

# Delay in seconds before each LLM request to avoid rate limits (e.g. Groq 429)
LLM_REQUEST_DELAY_SECONDS = float(
    os.environ.get("LLM_REQUEST_DELAY_SECONDS", "1.0")
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
    """Handle POST /api/chat. Uses Groq when GROQ_API_KEY is set.
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
    from agent_prompts import get_system_message
    import user_context_loader

    # Build system message: system_context + environment_summary + user_context + skills
    system_context_text = ""
    user_context = None
    environment_summary = ""
    try:
        system_context_text = user_context_loader.load_system_context(system_context_path)
        user_context = user_context_loader.load_user_context()
        environment_summary = user_context_loader.load_environment_summary()
    except Exception:
        pass
    if not (system_context_text or "").strip():
        system_context_text = (
            "You are ComfyUI Assistant. Help users with ComfyUI workflows. "
            "Use getWorkflowInfo, addNode, removeNode, connectNodes, setNodeWidgetValue, fillPromptNode when needed. "
            "Reply in the user's language. For greetings only, reply with text; do not call tools."
        )

    # Add system message if not present
    has_system = any(msg.get("role") == "system" for msg in openai_messages)
    if not has_system:
        openai_messages.insert(0, get_system_message(system_context_text, user_context, environment_summary))
    
    message_id = f"msg_{uuid.uuid4().hex}"

    placeholder = (
        "Chat API is not configured. Set GROQ_API_KEY in .env (copy from .env.example)."
    )

    if not GROQ_API_KEY:
        async def stream_placeholder():
            for chunk in _stream_ai_sdk_text(placeholder, message_id):
                yield chunk.encode("utf-8")
        resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
        await resp.prepare(request)
        async for chunk in stream_placeholder():
            await resp.write(chunk)
        return resp

    # Slash commands are handled client-side. If one slips through, avoid calling the LLM.
    raw_last_user = _get_last_user_text(messages).strip()
    if raw_last_user.startswith("/"):
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

    # Call OpenAI-compatible API (Groq, OpenAI, Together, Ollama, etc.) and stream response
    from openai import AsyncOpenAI
    # Limit retries on 429 so we fail fast and show a clear message instead of long waits
    client = AsyncOpenAI(
        api_key=GROQ_API_KEY,
        base_url=OPENAI_API_BASE_URL,
        max_retries=2,
    )

    # Debug log: request to LLM
    if logger.isEnabledFor(logging.DEBUG):
        roles = [m.get("role", "?") for m in openai_messages]
        sys_len = 0
        last_user = ""
        for m in openai_messages:
            if m.get("role") == "system":
                c = m.get("content") or ""
                sys_len = len(c)
            if m.get("role") == "user":
                last_user = (m.get("content") or "")[:200]
        logger.debug(
            "LLM request: messages=%s roles=%s system_len=%s last_user_preview=%s",
            len(openai_messages),
            roles,
            sys_len,
            repr(last_user[:80] + "..." if len(last_user) > 80 else last_user),
        )

    async def stream_groq():
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
        # Capture finish_reason from the LLM streaming response (last chunk)
        llm_finish_reason = None

        yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

        try:
            await asyncio.sleep(LLM_REQUEST_DELAY_SECONDS)
            stream = await client.chat.completions.create(
                model=GROQ_MODEL,
                messages=openai_messages,
                tools=TOOLS_DEFINITIONS,
                tool_choice="auto",
                stream=True,
            )

            async for chunk in stream:
                choice = chunk.choices[0] if chunk.choices else None
                if not choice:
                    continue

                # Last chunk carries finish_reason (e.g. "stop", "tool_calls")
                if choice.finish_reason:
                    llm_finish_reason = choice.finish_reason

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

            # Debug log: response from LLM
            if logger.isEnabledFor(logging.DEBUG):
                full_text = "".join(response_text_parts)
                logger.debug(
                    "LLM response: text_len=%s text_preview=%s tool_calls=%s",
                    len(full_text),
                    repr(full_text[:150] + "..." if len(full_text) > 150 else full_text),
                    response_tool_calls,
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

    resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
    await resp.prepare(request)
    async for chunk in stream_groq():
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
