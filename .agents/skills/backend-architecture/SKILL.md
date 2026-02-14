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
| `__init__.py` | Entry point + orchestrator: route registration and composition of specialized backend modules |
| `message_transforms.py` | Core layer: pure message transformations across UI/OpenAI/Anthropic/CLI formats |
| `context_management.py` | Core layer: context trimming, truncation, token estimation, and compaction |
| `chat_utilities.py` | Core/API helper layer: shared chat helpers and context-too-large detection |
| `provider_streaming.py` | Provider layer: provider-specific streaming generators (OpenAI/Anthropic/CLI adapters) |
| `cli_providers.py` | Provider layer: CLI binary discovery for claude/codex/gemini providers |
| `sse_streaming.py` | API layer: AI SDK SSE headers and event serialization helpers |
| `slash_commands.py` | Features layer: slash command handling (`/provider`, `/skill`) |
| `api_handlers.py` | Environment, docs, and skills API handlers (factory pattern via `create_handlers`) |
| `agent_prompts.py` | `get_system_message()` -- assembles system_context + environment + user_context |
| `tools_definitions.py` | `TOOLS` list in OpenAI function calling format; `get_tools()`, `get_tool_names()` |
| `user_context_loader.py` | `load_system_context()`, `load_user_context()`, `load_environment_summary()`, `load_skills()` |
| `user_context_store.py` | SQLite store (`context.db`): rules, preferences, onboarding state |
| `provider_store.py` | SQLite store (`providers.db`): provider CRUD, validation, active provider |
| `provider_manager.py` | Runtime provider selection, DB/env fallback, provider connection tests |
| `environment_scanner.py` | `scan_environment()`, node/package/model scanning, search, cache management |
| `skill_manager.py` | Create/list/delete/update user skills in `user_context/skills/` |
| `documentation_resolver.py` | Resolve documentation for node types and topics |

## Refactored Module Structure

### Layered separation of concerns

```
Core Layer
├── message_transforms.py
├── context_management.py
└── chat_utilities.py

Provider Layer
├── provider_streaming.py
└── cli_providers.py

Features Layer
├── slash_commands.py
└── sse_streaming.py

Orchestrator
└── __init__.py (wires modules, registers routes, selects provider path)
```

### Module dependency graph

```
__init__.py
├── message_transforms.py
├── context_management.py
├── chat_utilities.py
├── provider_streaming.py
│   ├── message_transforms.py
│   ├── context_management.py
│   └── sse_streaming.py
├── cli_providers.py
├── sse_streaming.py
└── slash_commands.py
```

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
| `/api/providers/status` | GET | provider handlers | Wizard status / first-time check |
| `/api/providers` | GET/POST | provider handlers | List/create providers |
| `/api/providers/{name}` | PATCH/DELETE | provider handlers | Update/delete provider |
| `/api/providers/{name}/activate` | POST | provider handlers | Set active provider |
| `/api/providers/{name}/test` | POST | provider handlers | Test saved provider |
| `/api/providers/test-config` | POST | provider handlers | Test unsaved config payload |
| `/api/providers/cli-status` | GET | provider handlers | Detect CLI availability/path |

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `LLM_PROVIDER` | auto-detect | Optional provider selector: `openai`, `anthropic`, `claude_code`, `codex`, or `gemini_cli` |
| `OPENAI_API_KEY` | (optional) | OpenAI-compatible provider API key |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI-compatible model name |
| `OPENAI_API_BASE_URL` | `https://api.openai.com/v1` | Any OpenAI-compatible provider URL |
| `ANTHROPIC_API_KEY` | (optional) | Anthropic API key for direct Messages API calls |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-5` | Anthropic model name |
| `ANTHROPIC_BASE_URL` | `https://api.anthropic.com` | Anthropic API URL |
| `ANTHROPIC_MAX_TOKENS` | `4096` | Anthropic max output tokens |
| `CLAUDE_CODE_COMMAND` | `claude` | Claude Code CLI executable |
| `CLAUDE_CODE_MODEL` | (empty) | Optional Claude Code model alias |
| `CODEX_COMMAND` | `codex` | Codex CLI executable |
| `CODEX_MODEL` | (empty) | Optional Codex model alias |
| `GEMINI_CLI_COMMAND` | `gemini` | Gemini CLI executable |
| `GEMINI_CLI_MODEL` | (empty) | Optional Gemini model name |
| `CLI_PROVIDER_TIMEOUT_SECONDS` | `180` | Timeout for CLI provider subprocess calls |
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
Primary path: configure providers in the wizard (`/provider-settings`) and switch with:
- `/provider list`
- `/provider set <name>`

Fallback path: set `LLM_PROVIDER` in `.env`:
- `openai`: use `OPENAI_API_KEY` (+ optional `OPENAI_API_BASE_URL`, `OPENAI_MODEL`)
- `anthropic`: use `ANTHROPIC_API_KEY` (+ optional `ANTHROPIC_MODEL`)
- `claude_code`: use local `claude` CLI (authenticated)
- `codex`: use local `codex` CLI (authenticated)
- `gemini_cli`: use local `gemini` CLI (authenticated)

If no active DB provider exists, backend falls back to `.env` auto-selection.

## Related Skills

- `architecture-overview` -- high-level system map and flow diagrams
- `backend-tools-declaration` -- how tools are declared and synced
- `system-and-user-context` -- system prompt assembly details
- `environment-and-models` -- environment scanning and caching
