# System Architecture

This document explains how ComfyUI Assistant is structured and how the pieces work together. Read this first if you're new to the codebase.

> **Agent skill**: For machine-optimized reference, see [`.agents/skills/architecture-overview/SKILL.md`](../../.agents/skills/architecture-overview/SKILL.md).

---

## What is ComfyUI Assistant?

ComfyUI Assistant is an AI-powered chat panel that lives inside ComfyUI's bottom panel. It connects a React frontend (using the assistant-ui library) to an LLM (via OpenAI-compatible provider or any OpenAI-compatible API) and gives the LLM tools to manipulate the ComfyUI graph, query the environment, and execute workflows. The result is an agentic assistant that can build and modify workflows through natural conversation.

---

## System diagram

```
┌──────────────────────────────────────────────────────────┐
│                     ComfyUI (Host)                       │
│  window.app  ·  graph API  ·  bottomPanelTabs            │
└──────────┬───────────────────────────────┬───────────────┘
           │ DOM / JS API                  │ aiohttp routes
┌──────────▼──────────────┐    ┌───────────▼───────────────┐
│    React Frontend       │    │     Python Backend        │
│  assistant-ui/react     │◄──►│  __init__.py (entry)      │
│  useChatRuntime         │SSE │  api_handlers.py          │
│  Tool implementations   │    │  agent_prompts.py         │
│  Slash commands          │    │  tools_definitions.py     │
└─────────────────────────┘    └───────────┬───────────────┘
                                           │ OpenAI-compat API
                               ┌───────────▼───────────────┐
                               │    LLM Provider (OpenAI-compatible provider)    │
                               │  Streaming + tool calling │
                               └───────────────────────────┘
```

There are three layers:

1. **ComfyUI (host)** provides the runtime environment: the graph editor, `window.app` JS API, and the bottom panel where the assistant lives.
2. **React frontend** renders the chat UI, executes tools against `window.app`, and manages the agentic loop.
3. **Python backend** handles chat requests, assembles the system prompt, calls the LLM, and streams responses as SSE.

The LLM provider (OpenAI-compatible provider by default) is external and accessed through an OpenAI-compatible API.

---

## How a chat message flows end-to-end

Here is what happens from the moment a user types a message to when they see the response:

1. **User types a message** in the bottom panel composer and presses Enter.
2. **The frontend** sends a `POST /api/chat` request with the full message history in AI SDK UIMessage format.
3. **The backend** (`chat_api_handler` in `__init__.py`) processes the request:
   - Converts UIMessages to OpenAI format (`_ui_messages_to_openai`)
   - Loads system context from `system_context/` files
   - Loads the environment summary (installed nodes, models, packages)
   - Loads user context (rules, personality, goals, skills from `user_context/`)
   - Assembles the full system message via `get_system_message()` in `agent_prompts.py`
   - Calls the LLM with streaming enabled and tool definitions attached
4. **The backend streams the response** as Server-Sent Events (SSE) using the AI SDK UI Message Stream v1 format.
5. **The frontend runtime** receives the SSE events and builds message parts: text, reasoning blocks, and tool calls.
6. **If the LLM made tool calls**, the frontend executes them (graph tools run against `window.app`; environment tools call backend APIs) and appends the results to the message history.
7. **The agentic loop kicks in**: if the last message part is a tool call result, `shouldResubmitAfterToolResult` triggers an automatic resubmit back to step 2 so the LLM can process the results.
8. **The loop ends** when the LLM responds with text only (no tool calls).

---

## How tool calls work

Tool calls are the mechanism that lets the LLM take actions in ComfyUI. Tools are declared in two places that must stay in sync: the Python backend (so the LLM knows what's available) and the TypeScript frontend (so the tools can actually execute).

```
LLM (OpenAI-compatible provider)                    Backend                Frontend
    │                             │                      │
    ├─ tool_call(addNode,{...}) ──►                      │
    │                             ├─ SSE: tool-input ───►│
    │                             │   -available          │
    │                             │                      ├─ execute tool
    │                             │                      │  (window.app access)
    │                             │                      ├─ append result
    │                             │                      │  to message
    │                             │◄─── resubmit ────────┤
    │◄── messages + tool_result ──┤                      │
    ├─ text("Done!") ─────────────►                      │
    │                             ├─ SSE: text-delta ───►│
    │                             │                      ├─ render text
```

1. The LLM decides to call a tool (e.g., `addNode`) and includes the tool call in its response.
2. The backend streams the tool call as a `tool-input-available` SSE event.
3. The frontend receives it and executes the corresponding implementation. Graph tools (like `addNode`) use `window.app.graph` directly. Environment tools (like `searchInstalledNodes`) make `fetch()` calls to backend API endpoints.
4. The result is appended to the message history as a tool-result message part.
5. The agentic loop resubmits the conversation. The backend converts the tool result to an OpenAI `tool` role message so the LLM can see the outcome.
6. The LLM processes the result and either calls more tools or responds with text.

---

## The agentic loop

The agentic loop is what makes the assistant "think in steps" rather than giving a single response. It lives in `ui/src/App.tsx`:

- **`AssistantChatTransport`** handles SSE communication with `/api/chat`.
- **`useChatRuntime`** manages state, messages, and threading.
- **`sendAutomaticallyWhen: shouldResubmitAfterToolResult`** is the key setting. The `shouldResubmitAfterToolResult` function checks whether the last message part is a tool invocation. If it is, the runtime automatically resubmits the full conversation to the backend, which calls the LLM again.
- The loop continues until the LLM responds with text only (no tool calls), at which point the response is displayed to the user.

This means the LLM can chain multiple tool calls in sequence: add a node, connect it, set widget values, then respond with a summary -- all in a single conversation turn.

---

## Where to look

| Concept | Primary file(s) |
|---------|-----------------|
| Backend entry point, route registration | `__init__.py` |
| Chat handler, SSE streaming | `__init__.py` (`chat_api_handler`) |
| System message assembly | `agent_prompts.py` |
| Tool definitions (backend, for LLM) | `tools_definitions.py` |
| Environment/docs/skills API handlers | `api_handlers.py` |
| Context loading (system, user, environment) | `user_context_loader.py` |
| Environment scanning and caching | `environment_scanner.py` |
| User data store (SQLite) | `user_context_store.py` |
| Skill management | `skill_manager.py` |
| Frontend entry point, ComfyUI registration | `ui/src/main.tsx` |
| Runtime setup, agentic loop | `ui/src/App.tsx` |
| Tool registry, definitions, implementations | `ui/src/tools/index.ts`, `ui/src/tools/definitions/`, `ui/src/tools/implementations/` |
| Chat UI components | `ui/src/components/assistant-ui/thread.tsx` |
| Terminal theme | `ui/src/components/assistant-ui/terminal-theme.css` |

---

## Files to read first

If you're new to the codebase, read these files in this order:

1. **`.agents/project-context.md`** -- Overview, stack, directory structure
2. **`__init__.py`** -- Backend entry point, route registration, chat handler
3. **`ui/src/main.tsx`** -- Frontend entry, ComfyUI extension registration
4. **`ui/src/App.tsx`** -- Runtime setup, agentic loop, onboarding
5. **`tools_definitions.py`** -- All tools the LLM can call
6. **`ui/src/tools/index.ts`** -- Frontend tool registry and implementations
7. **`agent_prompts.py`** -- System message assembly

---

## Related docs

- [Backend](backend.md) -- Python modules, API endpoints, SSE streaming
- [Context and environment](context-and-environment.md) -- System prompt assembly, environment scanning
- [Frontend](frontend.md) -- React components, ComfyUI integration, theme
- [Tools](tools.md) -- Step-by-step guide for adding and modifying tools
- [Standards and conventions](standards-and-conventions.md) -- Code style, Git, security rules
