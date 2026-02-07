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
logger.setLevel(logging.DEBUG)

# Import from current directory
current_dir = os.path.dirname(__file__)
import sys
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import agent_prompts
from agent_prompts import get_system_message
import user_context_store


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

# AI SDK UI Message Stream headers (required by AssistantChatTransport)
UI_MESSAGE_STREAM_HEADERS = {
    "Content-Type": "text/event-stream",
    "Cache-Control": "no-cache",
    "Connection": "keep-alive",
    "X-Vercel-AI-UI-Message-Stream": "v1",
}

# Tools definitions for OpenAI Function Calling
TOOLS_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "addNode",
            "description": "Add a new node to the ComfyUI workflow",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeType": {
                        "type": "string",
                        "description": "Node type to add (e.g., 'KSampler', 'CheckpointLoaderSimple')"
                    },
                    "position": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}
                        },
                        "description": "Optional position on canvas. Leave empty to use automatic positioning that avoids overlaps."
                    }
                },
                "required": ["nodeType"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "removeNode",
            "description": "Remove a node from the workflow",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeId": {
                        "type": "number",
                        "description": "ID of the node to remove"
                    }
                },
                "required": ["nodeId"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "connectNodes",
            "description": "Connect output of one node to input of another",
            "parameters": {
                "type": "object",
                "properties": {
                    "sourceNodeId": {"type": "number"},
                    "sourceSlot": {"type": "number"},
                    "targetNodeId": {"type": "number"},
                    "targetSlot": {"type": "number"}
                },
                "required": ["sourceNodeId", "sourceSlot", "targetNodeId", "targetSlot"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getWorkflowInfo",
            "description": "Get information about the current workflow state",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    }
]


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
            result.append({"role": "user", "content": _extract_content(msg)})

        elif role == "assistant":
            openai_msg = {"role": "assistant"}

            # Extract text content
            content = _extract_content(msg)
            if content:
                openai_msg["content"] = content

            # Extract tool calls and results from parts
            tool_calls = []
            tool_results = []
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

                    # Add tool call to assistant message
                    tool_calls.append({
                        "id": tool_call_id,
                        "type": "function",
                        "function": {
                            "name": tool_name,
                            "arguments": json.dumps(args) if args else "{}"
                        }
                    })

                    # If the tool has completed, add a tool result message
                    if state == "output-available" and "output" in part:
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps(part.get("output", {}))
                        })
                    elif state == "output-error":
                        tool_results.append({
                            "role": "tool",
                            "tool_call_id": tool_call_id,
                            "content": json.dumps({
                                "error": part.get("errorText", "Unknown error")
                            })
                        })

                # Legacy format: type == 'tool-call'
                elif part_type == "tool-call":
                    tool_calls.append({
                        "id": part.get("toolCallId", ""),
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
    openai_messages = _ui_messages_to_openai(messages)
    
    # Reload agent_prompts to pick up any changes (useful during development)
    importlib.reload(agent_prompts)
    from agent_prompts import get_system_message
    import user_context_loader

    # Build system message: system_context + user_context + skills (same injection mechanism)
    system_context_text = ""
    user_context = None
    try:
        system_context_text = user_context_loader.load_system_context(system_context_path)
        user_context = user_context_loader.load_user_context()
    except Exception:
        pass
    if not (system_context_text or "").strip():
        system_context_text = (
            "You are ComfyUI Assistant. Help users with ComfyUI workflows. "
            "Use getWorkflowInfo, addNode, removeNode, connectNodes when needed. "
            "Reply in the user's language. For greetings only, reply with text; do not call tools."
        )

    # Add system message if not present
    has_system = any(msg.get("role") == "system" for msg in openai_messages)
    if not has_system:
        openai_messages.insert(0, get_system_message(system_context_text, user_context))
    
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
        text_end_sent = False  # True after we emit text-end (must be before tool-input-available for client)
        # Buffer for accumulating tool call chunks
        tool_calls_buffer = {}
        # Accumulate assistant response for debug log
        response_text_parts = []
        response_tool_calls = []

        yield _sse_line({"type": "start", "messageId": message_id}).encode("utf-8")

        try:
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

                        # Start text part for cleaned content
                        if cleaned_text and not text_id:
                            text_id = f"msg_{uuid.uuid4().hex[:24]}"
                            yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")

                        if cleaned_text:
                            yield _sse_line({"type": "text-delta", "id": text_id, "delta": cleaned_text}).encode("utf-8")
                            text_sent = True
                            response_text_parts.append(cleaned_text)

                        buffer = ""
                    else:
                        # Stream normally if no complete thinking blocks yet
                        if not '<think>' in buffer:
                            if not text_id or text_id.startswith("msg_"):
                                text_id = f"msg_{uuid.uuid4().hex[:24]}"
                                yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
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
                                "started": False,
                                "completed": False
                            }
                        
                        tool_call_data = tool_calls_buffer[index]
                        
                        # Accumulate tool call data
                        if tool_call_delta.id:
                            tool_call_data["id"] = tool_call_delta.id
                        if tool_call_delta.function:
                            if tool_call_delta.function.name:
                                tool_call_data["name"] = tool_call_delta.function.name
                            if tool_call_delta.function.arguments:
                                args_delta = tool_call_delta.function.arguments
                                tool_call_data["arguments"] += args_delta
                                
                                # Emit tool-input-start if this is the first chunk
                                if not tool_call_data["started"] and tool_call_data["id"] and tool_call_data["name"]:
                                    yield _sse_line({
                                        "type": "tool-input-start",
                                        "toolCallId": tool_call_data["id"],
                                        "toolName": tool_call_data["name"]
                                    }).encode("utf-8")
                                    tool_call_data["started"] = True
                                
                                # Emit tool-input-delta for argument chunks
                                if tool_call_data["started"]:
                                    yield _sse_line({
                                        "type": "tool-input-delta",
                                        "toolCallId": tool_call_data["id"],
                                        "inputTextDelta": args_delta
                                    }).encode("utf-8")

            # Process any remaining buffer
            if buffer:
                reasoning_parts, cleaned_text = _parse_thinking_tags(buffer)

                for reasoning_text in reasoning_parts:
                    reasoning_id = f"reasoning_{uuid.uuid4().hex[:24]}"
                    yield _sse_line({"type": "reasoning-start", "id": reasoning_id}).encode("utf-8")
                    yield _sse_line({"type": "reasoning-delta", "id": reasoning_id, "delta": reasoning_text}).encode("utf-8")
                    yield _sse_line({"type": "reasoning-end", "id": reasoning_id}).encode("utf-8")

                if cleaned_text:
                    if not text_id or text_id.startswith("msg_"):
                        text_id = f"msg_{uuid.uuid4().hex[:24]}"
                        yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                    yield _sse_line({"type": "text-delta", "id": text_id, "delta": cleaned_text}).encode("utf-8")
                    text_sent = True
                    response_text_parts.append(cleaned_text)

            # If model returned only tool calls and no text, emit a short placeholder so the UI shows a message
            has_tool_calls = any(
                tc.get("id") and tc.get("name") for tc in tool_calls_buffer.values()
            )
            if has_tool_calls and not text_sent:
                placeholder = "Checking your workflow…"
                text_id = f"msg_{uuid.uuid4().hex[:24]}"
                yield _sse_line({"type": "text-start", "id": text_id}).encode("utf-8")
                yield _sse_line({"type": "text-delta", "id": text_id, "delta": placeholder}).encode("utf-8")
                text_sent = True
                response_text_parts.append(placeholder)

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
        yield _sse_line({"type": "finish", "finishReason": "stop"}).encode("utf-8")
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


# Register the chat API route (must be registered before static routes so /api/chat is handled)
server.PromptServer.instance.app.add_routes([
    web.post("/api/chat", chat_api_handler),
    web.get("/api/user-context/status", user_context_status_handler),
    web.post("/api/user-context/onboarding", user_context_onboarding_handler),
])

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