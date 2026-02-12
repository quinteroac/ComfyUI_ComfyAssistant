---
name: architecture-overview
description: High-level system map of ComfyUI Assistant -- read first to understand the project
version: 0.0.1
license: MIT
---

# Architecture Overview

Read this skill first to understand how the pieces fit together.

## System Diagram

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

## Files to Read First (in order)

1. `.agents/project-context.md` -- overview, stack, directory structure
2. `__init__.py` -- backend entry point, route registration, chat handler
3. `ui/src/main.tsx` -- frontend entry, ComfyUI extension registration
4. `ui/src/App.tsx` -- runtime setup, agentic loop, onboarding
5. `tools_definitions.py` -- all tools the LLM can call
6. `ui/src/tools/index.ts` -- frontend tool registry and implementations
7. `agent_prompts.py` -- system message assembly

## Chat Request Flow (end-to-end)

1. **User types message** in the bottom panel composer
2. **Frontend** sends POST `/api/chat` with full message history (AI SDK UIMessage format)
3. **Backend** (`chat_api_handler` in `__init__.py`):
   a. Converts UIMessages to OpenAI format (`_ui_messages_to_openai`)
   b. Loads system context (`load_system_context` from `user_context_loader.py`)
   c. Loads environment summary (`load_environment_summary`)
   d. Loads user context (`load_user_context`)
   e. Assembles system message (`get_system_message` from `agent_prompts.py`)
   f. Calls LLM (OpenAI-compatible provider) with streaming enabled + tool definitions
   g. Streams response as SSE (AI SDK UI Message Stream v1)
4. **Frontend runtime** receives SSE events, builds message parts (text, reasoning, tool calls)
5. If LLM returns **tool calls**: runtime executes tools from `ModelContext`, appends results
6. **Auto-resubmit** (`shouldResubmitAfterToolResult`): if last message part is a tool call, resubmit to get next LLM response -- this creates the agentic loop
7. Loop ends when LLM responds with **text only** (no tool calls)

## Tool Call Flow

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

## Runtime Architecture

- **Transport**: `AssistantChatTransport({ api: '/api/chat' })` -- handles SSE communication
- **Runtime**: `useChatRuntime({ transport })` -- manages state, messages, threading
- **Provider**: `AssistantRuntimeProvider` wraps the component tree
- **Tools**: `useComfyTools()` hook registers tools into `ModelContext`
- **Auto-resubmit**: `sendAutomaticallyWhen: shouldResubmitAfterToolResult` drives the agentic loop
- **Thread UI**: Custom `Thread` component with terminal-style rendering

## Related Skills

- `backend-architecture` -- Python modules and API details
- `backend-tools-declaration` -- Tool sync between frontend and backend
- `ui-integration` -- How React wires into ComfyUI
- `assistant-ui` -- Chat UI components and customization

## FAQ

### Which files should I read first to understand the project?
See "Files to Read First" above.

### How does a tool call move from the LLM to ComfyUI and back?
See "Tool Call Flow" diagram above. The LLM emits a tool_call, backend streams it as SSE, frontend executes it against `window.app`, appends the result, and resubmits.

### Where does the agentic loop live?
In `ui/src/App.tsx`. The `shouldResubmitAfterToolResult` function checks if the last message part is a tool invocation; if so, `sendAutomaticallyWhen` triggers a resubmit.

### What streaming format does the backend use?
AI SDK UI Message Stream v1 over SSE. Events: `start`, `text-start`, `text-delta`, `text-end`, `reasoning-*`, `tool-input-available`, `finish`, `[DONE]`.
