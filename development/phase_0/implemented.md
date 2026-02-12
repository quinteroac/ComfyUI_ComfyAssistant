# Phase 0 — Implemented (baseline)

This document describes **Phase 0 (Current MVP baseline)**. Phase 0 is the minimal assistant that was implemented before Phase 1 and Phase 2; it establishes chat + graph manipulation with no backend agent and no persistent user context.

Reference: [comfyui_assistant_development_phases.md](../../planning/comfyui_assistant_development_phases.md) (Phase 0 section).

---

## Delivered

### 1. Chat UI

- **UI:** Chat interface with threads, messages, markdown rendering, attachments.
- **Stack:** assistant-ui/react, Vercel AI SDK, React + TypeScript, Tailwind.
- **Location:** `ui/src/` (components, App, main entry).

### 2. LLM integration

- **API:** OpenAI-compatible (OpenAI-compatible provider default; configurable via `OPENAI_API_BASE_URL`, API key, model in `.env`).
- **Streaming:** Server-Sent Events (SSE) from backend to frontend.
- **Backend:** Chat handler in `__init__.py`; system message and tool definitions injected from `agent_prompts.py` and `tools_definitions.py`.

### 3. Tools (frontend-executed)

- **addNode** — Add nodes to the workflow.
- **removeNode** — Remove nodes by ID.
- **connectNodes** — Connect two nodes.
- **getWorkflowInfo** — Query workflow state (nodes, connections; node details optional).

Execution in frontend via `window.app` (ComfyUI graph API). Backend declares tools in OpenAI format and streams LLM response; no back agent.

### 4. Prompts and tool definitions

- **System message:** Built in `agent_prompts.py` (later extended by Phase 1 with `system_context/` and user context).
- **Tool declarations:** `tools_definitions.py` (OpenAI format); passed to LLM from `__init__.py` chat handler.

### 5. Out of scope (by design)

- No back agent, no `.agents/` shared context, no scan of `custom_nodes/` or `models/`.
- No persistent user context, no user skills, no onboarding.
- No node widget configuration (added in Phase 2), no workflow execution, no `apply_workflow_json`.

---

## File and route summary

| Item | Location / path |
|------|------------------|
| Frontend entry | `ui/src/main.tsx`, `ui/src/App.tsx` |
| Chat UI components | `ui/src/components/assistant-ui/` |
| Tool definitions (Zod) | `ui/src/tools/definitions/` |
| Tool implementations | `ui/src/tools/implementations/` |
| Tool registry | `ui/src/tools/index.ts` |
| Backend entry | `__init__.py` (routes, chat handler) |
| System prompt / assembly | `agent_prompts.py` |
| Tool declarations (OpenAI) | `tools_definitions.py` |
| Chat API | POST `/api/chat` (SSE stream) |
| Env config | `.env` (e.g. `OPENAI_API_KEY`, `OPENAI_API_BASE_URL`, `OPENAI_MODEL`) |

---

## Iteration log

- **Phase 0 baseline:** Chat UI, LLM (OpenAI-compatible), addNode/removeNode/connectNodes/getWorkflowInfo, SSE streaming, no user context. Phase 1 and Phase 2 build on this baseline.
