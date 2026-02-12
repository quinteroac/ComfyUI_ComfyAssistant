---
name: backend-architecture
description: Python backend modules, chat request lifecycle, SSE format, and API endpoints
version: 0.0.1
license: MIT
---

# Backend Architecture

The Python backend lives at the project root. ComfyUI loads `__init__.py` as a custom node extension and registers aiohttp routes.

## Module Map

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

## `chat_api_handler` Lifecycle

The main handler in `__init__.py` for POST `/api/chat`:

1. **Parse request** -- extract `messages` array from JSON body
2. **Convert messages** -- `_ui_messages_to_openai(messages)` transforms AI SDK UIMessage format to OpenAI chat completions format (handles tool invocations, states, legacy format)
3. **Reload prompts** -- `importlib.reload(agent_prompts)` for hot-reload during development
4. **Load context** -- `load_system_context()`, `load_environment_summary()`, `load_user_context()`
5. **Assemble system message** -- `get_system_message(system_context, user_context, env_summary)`
6. **Apply delay** -- `LLM_REQUEST_DELAY_SECONDS` (default 1.0s) rate limiting
7. **Call LLM** -- OpenAI-compatible API (OpenAI-compatible provider default) with streaming + tool definitions
8. **Stream SSE** -- emit AI SDK UI Message Stream v1 events
9. **Error handling** -- 429 rate limits get a friendly text response; other errors return 500

## SSE Format (AI SDK UI Message Stream v1)

Required headers:
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Vercel-AI-UI-Message-Stream: v1
```

Event sequence for a typical response:
```
data: {"type":"start","messageId":"msg_..."}
data: {"type":"reasoning-start","id":"reasoning_..."}     # if <think> tags
data: {"type":"reasoning-delta","id":"...","delta":"..."}
data: {"type":"reasoning-end","id":"reasoning_..."}
data: {"type":"text-start","id":"text_..."}
data: {"type":"text-delta","id":"text_...","delta":"I'll add a KSampler..."}
data: {"type":"text-end","id":"text_..."}
data: {"type":"tool-input-available","toolCallId":"call_...","toolName":"addNode","input":{...}}
data: {"type":"finish","finishReason":"tool-calls"}
data: [DONE]
```

Finish reasons: `stop`, `tool-calls`, `length`, `content-filter`.

## API Endpoints

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

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `OPENAI_API_KEY` | (required) | LLM provider API key |
| `OPENAI_MODEL` | `llama3-70b-8192` | Model name |
| `OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible provider URL |
| `LLM_REQUEST_DELAY_SECONDS` | `1.0` | Rate-limit delay before each LLM call |
| `COMFY_ASSISTANT_LOG_LEVEL` | `INFO` | Logging level |

## FAQ

### How do I add a new API endpoint?
1. Write an async handler function in `api_handlers.py` (signature: `async def handler(request: web.Request) -> web.Response`)
2. Add it to the dict returned by `create_handlers()`
3. Register the route in `register_routes()` (maps path + method to handler)
4. The route is automatically available when ComfyUI starts

### What happens when the UI sends a chat message?
See "chat_api_handler Lifecycle" above. Messages arrive as AI SDK UIMessages, get converted to OpenAI format, context is assembled, LLM is called with streaming, and SSE events flow back.

### How does the backend handle rate limiting?
Two ways: (1) `LLM_REQUEST_DELAY_SECONDS` adds a delay before each LLM call; (2) if OpenAI-compatible provider returns HTTP 429, the handler catches it and streams a friendly "Rate limited" text message instead of an error.

### How do I change the LLM provider?
Set `OPENAI_API_BASE_URL` in `.env` to any OpenAI-compatible endpoint (OpenAI-compatible provider, OpenAI, Together, Ollama, etc.) and set the API key in `OPENAI_API_KEY`.

## Related Skills

- `architecture-overview` -- high-level system map and flow diagrams
- `backend-tools-declaration` -- how tools are declared and synced
- `system-and-user-context` -- system prompt assembly details
- `environment-and-models` -- environment scanning and caching
