# Python Backend Guide

This document covers the Python backend: its modules, the chat request lifecycle, SSE streaming format, API endpoints, and how to add new endpoints and tools.

> **Agent skills**: For machine-optimized reference, see [`.agents/skills/backend-architecture/SKILL.md`](../../.agents/skills/backend-architecture/SKILL.md) and [`.agents/skills/backend-tools-declaration/SKILL.md`](../../.agents/skills/backend-tools-declaration/SKILL.md).

---

## Module map

The Python backend lives at the project root. ComfyUI loads `__init__.py` as a custom node extension and registers aiohttp routes.

| File | Purpose |
|------|---------|
| `__init__.py` | Entry point: route registration, `chat_api_handler`, SSE streaming, message conversion, auto-scan startup |
| `api_handlers.py` | Environment, docs, and skills API handlers (factory pattern via `create_handlers`) |
| `agent_prompts.py` | `get_system_message()` -- assembles system_context + environment + user_context |
| `tools_definitions.py` | `TOOLS` list in OpenAI function calling format; `get_tools()`, `get_tool_names()` |
| `user_context_loader.py` | `load_system_context()`, `load_user_context()`, `load_environment_summary()`, `load_skills()` |
| `user_context_store.py` | SQLite store (`context.db`): rules, preferences, onboarding state |
| `environment_scanner.py` | `scan_environment()`, node/package/model scanning, search, cache management |
| `skill_manager.py` | Create/list/delete/update user skills in `user_context/skills/` |
| `documentation_resolver.py` | Resolve documentation for node types and topics |

---

## Chat request lifecycle

The main handler is `chat_api_handler` in `__init__.py`, triggered by `POST /api/chat`. Here is what happens step by step:

1. **Parse request** -- Extract the `messages` array from the JSON body.
2. **Convert messages** -- `_ui_messages_to_openai(messages)` transforms AI SDK UIMessage format to OpenAI chat completions format. This handles tool invocations, tool states, and legacy format differences.
3. **Reload prompts** -- `importlib.reload(agent_prompts)` enables hot-reload during development so you can edit `agent_prompts.py` without restarting ComfyUI.
4. **Load context** -- Three calls to `user_context_loader.py`:
   - `load_system_context()` reads `system_context/*.md` and `system_context/skills/*/SKILL.md`
   - `load_environment_summary()` reads the cached environment summary
   - `load_user_context()` reads rules, personality, goals, and user skills
5. **Assemble system message** -- `get_system_message(system_context, user_context, env_summary)` combines everything into one system message.
6. **Apply delay** -- `LLM_REQUEST_DELAY_SECONDS` (default 1.0s) rate limiting to avoid hitting API limits.
7. **Call LLM** -- OpenAI-compatible API call (OpenAI-compatible provider by default) with streaming enabled and the `TOOLS` list from `tools_definitions.py`.
8. **Stream SSE** -- Emit events in AI SDK UI Message Stream v1 format (see below).
9. **Error handling** -- HTTP 429 (rate limit) from the provider gets a friendly text response; other errors return HTTP 500.

---

## SSE streaming format

The backend uses the AI SDK UI Message Stream v1 format over Server-Sent Events. The required HTTP headers are:

```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Vercel-AI-UI-Message-Stream: v1
```

A typical event sequence looks like this:

```
data: {"type":"start","messageId":"msg_..."}
data: {"type":"reasoning-start","id":"reasoning_..."}
data: {"type":"reasoning-delta","id":"...","delta":"Let me think..."}
data: {"type":"reasoning-end","id":"reasoning_..."}
data: {"type":"text-start","id":"text_..."}
data: {"type":"text-delta","id":"text_...","delta":"I'll add a KSampler node..."}
data: {"type":"text-end","id":"text_..."}
data: {"type":"tool-input-available","toolCallId":"call_...","toolName":"addNode","input":{...}}
data: {"type":"finish","finishReason":"tool-calls"}
data: [DONE]
```

The `reasoning-*` events only appear when the LLM uses `<think>` tags. Finish reasons: `stop`, `tool-calls`, `length`, `content-filter`.

---

## API endpoints

| Endpoint | Method | Handler | Purpose |
|----------|--------|---------|---------|
| `/api/chat` | POST | `chat_api_handler` | Main chat (SSE stream) |
| `/api/user-context/status` | GET | `user_context_status_handler` | Onboarding status check |
| `/api/user-context/onboarding` | POST | `user_context_onboarding_handler` | Save onboarding data |
| `/api/environment/scan` | POST | `environment_scan_handler` | Trigger full environment scan |
| `/api/environment/summary` | GET | `environment_summary_handler` | Brief text for prompt injection |
| `/api/environment/nodes` | GET | `environment_nodes_handler` | Search nodes (`?q=&category=&limit=`) |
| `/api/environment/models` | GET | `environment_models_handler` | List models (`?category=`) |
| `/api/environment/packages` | GET | `environment_packages_handler` | List custom node packages |
| `/api/environment/docs` | GET | `environment_docs_handler` | Fetch docs (`?topic=&source=`) |
| `/api/user-context/skills` | POST | `skills_handler` | Create user skill |
| `/api/user-context/skills` | GET | `skills_handler` | List user skills |
| `/api/user-context/skills/{slug}` | DELETE | `skill_delete_handler` | Delete skill |
| `/api/user-context/skills/{slug}` | PATCH | `skill_update_handler` | Update skill |

---

## How to add a new endpoint

1. Write an async handler function in `api_handlers.py`:

   ```python
   async def my_new_handler(request: web.Request) -> web.Response:
       """Handle GET /api/my-new-endpoint."""
       data = {"message": "hello"}
       return web.json_response(data)
   ```

2. Add the handler to the dict returned by `create_handlers()` in `api_handlers.py`.
3. Register the route in `register_routes()` in `__init__.py` (maps path + HTTP method to handler).
4. The route is automatically available when ComfyUI starts. No other configuration needed.

---

## Environment variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | (required) | LLM provider API key |
| `OPENAI_MODEL` | `llama3-70b-8192` | Model name |
| `OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible provider URL |
| `LLM_REQUEST_DELAY_SECONDS` | `1.0` | Rate-limit delay before each LLM call |
| `COMFY_ASSISTANT_LOG_LEVEL` | `INFO` | Logging level |

To change the LLM provider, set `OPENAI_API_BASE_URL` to any OpenAI-compatible endpoint (OpenAI-compatible provider, OpenAI, Together, Ollama, etc.) and set the corresponding API key in `OPENAI_API_KEY`.

---

## How tools are declared

Tools are defined in OpenAI function calling format in `tools_definitions.py`:

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "addNode",
            "description": "Adds a node to the workflow...",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeType": {"type": "string", "description": "..."},
                    "position": {
                        "type": "object",
                        "properties": {"x": {"type": "number"}, "y": {"type": "number"}}
                    }
                },
                "required": ["nodeType"]
            }
        }
    },
    ...
]
```

`get_tools()` returns the full list. `get_tool_names()` returns just the name strings.

The LLM only sees the backend definitions. The frontend has matching Zod schemas and implementations that actually execute the tools. Both sides must stay in sync -- see [tools.md](tools.md) for the full workflow.

---

## How to add a new tool (backend side)

1. Add a new entry to the `TOOLS` list in `tools_definitions.py` using the OpenAI function calling format. Use camelCase for the tool name and match parameter names/types exactly with what the frontend will expect.
2. If the tool needs a backend API endpoint (for environment or data queries), add the endpoint as described in "How to add a new endpoint" above.
3. Add usage guidance in `system_context/skills/` so the LLM knows when and how to use the new tool.

The frontend side (Zod schema, implementation, registry) is covered in [tools.md](tools.md).

---

## How do I...

**...change the LLM provider?**
Set `OPENAI_API_BASE_URL` in `.env` to any OpenAI-compatible endpoint and set the API key in `OPENAI_API_KEY`.

**...handle rate limiting differently?**
Two mechanisms exist: (1) `LLM_REQUEST_DELAY_SECONDS` adds a delay before each LLM call; (2) if the provider returns HTTP 429, the handler catches it and streams a friendly "Rate limited" text message. Edit `chat_api_handler` in `__init__.py` to change either behavior.

**...hot-reload the system prompt during development?**
It already works. The backend calls `importlib.reload(agent_prompts)` on every chat request, so edits to `agent_prompts.py` take effect immediately.

**...add a new type of context to the system prompt?**
See [context-and-environment.md](context-and-environment.md) for details on the context pipeline.

---

## Related docs

- [Architecture](architecture.md) -- System overview and request flow diagrams
- [Context and environment](context-and-environment.md) -- System prompt assembly, environment scanning
- [Tools](tools.md) -- Full step-by-step guide for adding tools (frontend + backend)
- [Frontend](frontend.md) -- React components and ComfyUI integration
