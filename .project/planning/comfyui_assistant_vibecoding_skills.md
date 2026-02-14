## ComfyUI Assistant – Vibecoding Skills Plan

This document defines which Agent Skills should exist under `.agents/skills/` so that both humans and agents can quickly understand how ComfyUI Assistant is built, what modules to touch, and how the main features work.

The focus is to cover:
- UI‑related behaviour
- Backend behaviour
- Overall architecture and patterns
- Data model (system_context, user_context, environment)

All skills should be written in **English**, follow the Agent Skills standard (`SKILL.md` with YAML frontmatter), and be **action‑oriented** (“how do I change X?”).

---

## 1. UI‑Related Skills

### 1.1 `assistant-ui` skill (existing, may need updates)

**Goal**: Explain how the chat UI is structured and how it integrates into ComfyUI.

- Scope:
  - Components under `ui/src/components/assistant-ui/`
  - How assistant-ui/react is configured (runtime, streaming, tool calling)
  - Console‑style layout, hidden thread list, and any custom UI decisions
- Questions it should answer:
  - “Where do I change how messages look or how tools are rendered?”
  - “Where is the bottom panel chat registered and configured?”

### 1.2 `ui-integration` skill (new)

**Goal**: Show how the React extension is wired into ComfyUI.

- Scope:
  - Entry points (`ui/src/main.tsx`, `App.tsx`)
  - How the bottom panel tab is registered
  - How the UI accesses `window.app` (directly or via runtime)
- Questions:
  - “Where do I change the tab name/icon/placement?”
  - “How do I add new UI panels or controls that still talk to the assistant?”

---

## 2. Backend‑Related Skills

### 2.1 `backend-architecture` skill (new)

**Goal**: Describe the Python modules and the chat request flow.

- Scope:
  - `__init__.py` (extension entry point)
  - `api_handlers.py` (chat + environment endpoints)
  - `agent_prompts.py` (system message assembly)
  - `tools_definitions.py` (backend tool declarations)
- Questions:
  - “What happens when the UI sends a chat message?”
  - “Where do I add or modify an API endpoint?”

### 2.2 `backend-tools-declaration` skill (new)

**Goal**: Explain how tools are declared on the backend and synced with the frontend.

- Scope:
  - Structure and patterns in `tools_definitions.py`
  - Mapping to OpenAI tool schema
  - How to keep Python + TypeScript tool definitions in sync
- Questions:
  - “I added a tool in TS – what must I change in Python?”
  - “Where do I change a tool’s name, description, or parameters?”

---

## 3. System Understanding (Architecture & Patterns)

### 3.1 `architecture-overview` skill (new)

**Goal**: Provide a high‑level map of the system and how pieces fit together.

- Scope:
  - Summary of `.agents/project-context.md`
  - Frontend ↔ backend ↔ ComfyUI graph flow
  - Where the assistant runtime lives and how streaming works
- Questions:
  - “Which files should I read first to understand the project?”
  - “How does a tool call move from the LLM to ComfyUI and back?”

### 3.2 `patterns-and-conventions` skill (new, thin wrapper)

**Goal**: Give a short, opinionated summary of `.agents/conventions.md` for quick consumption by agents.

- Scope:
  - Security‑first rules (no eval, no secrets, validation)
  - TypeScript + Python style highlights
  - Git and documentation rules (planning vs development vs `.agents/`)
- Questions:
  - “What are the non‑negotiable rules when editing this repo?”
  - “Where do planning docs vs implementation docs vs skills live?”

---

## 4. Data Model Skills (system_context, user_context, environment)

### 4.1 `system-and-user-context` skill (new)

**Goal**: Explain how system_context and user_context are structured and injected.

- Scope:
  - `system_context/` layout and loading order
  - `user_context/` (SOUL, goals, skills, environment cache)
  - How `user_context_loader.py` composes the final prompt
- Questions:
  - “Where do base instructions live vs user preferences?”
  - “How do I add a new kind of user context or tweak injection order?”

### 4.2 `environment-and-models` skill (new)

**Goal**: Document how installed nodes, custom nodes, and models are scanned and exposed.

- Scope:
  - `environment_scanner.py` and the `user_context/environment/` JSON files
  - Environment‑related tools (`refreshEnvironment`, `searchInstalledNodes`, `getAvailableModels`, `readDocumentation`)
  - How environment info is surfaced to the LLM
- Questions:
  - “How does the assistant know which nodes and models are available?”
  - “Where do I change or extend what gets scanned and cached?”

---

## 5. Next Steps

1. Create or update the skills listed above under `.agents/skills/`, following the Agent Skills standard.
2. When modifying UI, backend, or environment logic, update the corresponding skill in the same change.
3. Use this document as the checklist when asking an agent to “review vibecoding skills” or to “add a new skill” for a touched area.
4. Update `.agents/conventions.md` to reference these skills explicitly and require agents to understand and use the relevant skill before making changes to that part of the system.
