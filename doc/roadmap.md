# Roadmap

This document summarizes the development roadmap for ComfyUI Assistant. The project is built in **phases**: each phase delivers a working increment and sets the base for the next.

**Status overview**

| Phase | Status   | Focus |
|-------|----------|--------|
| **0** | Done     | MVP: chat + graph tools |
| **1** | Done     | User context and manual skills |
| **2** | Done     | Node configuration and prompts |
| **3** | Done     | Environment awareness, search, create_skill |
| **4** | Done     | Workflow execution and complex workflows |
| **5a** | Done     | Bottom panel + terminal UI |
| **5b** | Done     | Slash commands, named sessions |
| **5** | Planned  | Polish (Manager, multi-provider UI, i18n, security) |
| **8** | Done     | Research tools (web search, fetch, registry, examples) |

---

## Phase 0 — MVP (baseline) — Done

**Goal:** Minimal assistant: chat and graph manipulation, no persistent context.

**Delivered:**

- Chat UI (threads, messages, markdown).
- OpenAI-compatible LLM (OpenAI-compatible provider or any provider via `.env`).
- **Tools:** addNode, removeNode, connectNodes, getWorkflowInfo (all run in the browser on the ComfyUI graph).
- System prompts and tool definitions in the backend.

**Out of scope:** User context, skills, node widget configuration, workflow execution.

---

## Phase 1 — User context and manual skills — Done

**Goal:** Persist user context (rules, preferences, personality) and support **manually created** user skills. Optional first-time onboarding.

**Delivered:**

- **User workspace** `user_context/`: SQLite store (rules, preferences), SOUL.md, goals.md.
- **Skills:** `user_context/skills/` — one directory per skill with SKILL.md (you create and edit them by hand).
- User context and skills are loaded into the system prompt so the assistant follows your preferences and skills.
- **Onboarding:** Optional first-time flow (personality, goals, experience); can be skipped.

**Out of scope:** Agent-driven skill creation (planned for Phase 3).

See [Configuration](configuration.md) and [User skills](skills.md).

---

## Phase 2 — Node configuration and prompts — Done

**Goal:** Let the assistant configure node widgets and set prompt text, so you can ask for full workflows in one go.

**Delivered:**

- **setNodeWidgetValue** — Set any widget on a node (steps, cfg, seed, sampler, scheduler, denoise, width, height, etc.).
- **fillPromptNode** — Set the text of a CLIPTextEncode (prompt) node.
- **getWorkflowInfo** extended with widget names and values when you need details.
- System prompts updated so the assistant uses these tools (e.g. “create a txt2img workflow with 20 steps and prompt ‘a cat’”).

See [Base tools](base-tools.md).

---

## Phase 3 — Environment awareness, search, and create_skill — Done

**Goal:** Backend modules that scan the ComfyUI installation and expose context to the assistant. **create_skill** so the assistant can create and save user skills when you ask it to "remember" something.

**Delivered:**

- **Environment scanner** — Backend Python module that scans `nodes.NODE_CLASS_MAPPINGS`, `custom_nodes/` directory, and `folder_paths` models. Results cached to `user_context/environment/*.json` with a brief summary injected into the system prompt.
- **refreshEnvironment** — Tool to rescan the installation and update cached context.
- **searchInstalledNodes** — Search installed node types by name, category, or package.
- **readDocumentation** — Fetch documentation for a node type or topic (from `NODE_CLASS_MAPPINGS`, custom node READMEs, system context).
- **createSkill** — The assistant can create and persist a user skill (e.g. "remember to always use Preview Image instead of Save Image") into `user_context/skills/`.
- **Auto-scan on startup** — Non-blocking initial scan after ComfyUI loads.
- **API handlers extracted** to `api_handlers.py` for maintainability.

See [Phase 3 implementation notes](../development/phase_3/implemented.md).

---

## Phase 4 — Workflow execution and complex workflows — Done

**Goal:** Run the workflow from the assistant and load full workflows from a description or JSON.

**Delivered:**

- **executeWorkflow** — Queue the current workflow, wait for completion via ComfyUI events (`executed`, `execution_success`, `execution_error`, `execution_interrupted`), return status and output summary (images, errors, timing).
- **applyWorkflowJson** — Load a complete workflow in one call (API format or frontend format with nodes/links), replacing the current graph. For API format, pre-validates node types and ensures `_meta.title`; for frontend format uses `loadGraphData` (e.g. templates, exported workflows).
- System prompt skill (`05_workflow_execution/SKILL.md`) with API format specification, example txt2img workflow, build-then-run pattern, and guidelines for verifying node types and models before generating workflows.

See [Phase 4 implementation notes](../development/phase_4/implemented.md).

---

## Phase 5a — Bottom panel + terminal UI — Done

**Goal:** Move the assistant to the bottom panel with a terminal-style aesthetic.

**Delivered:**

- **Layout:** Replaced sidebar tab with bottom panel tab registration.
- **Terminal UI:** Monospace font, flat blocks, compact spacing, `›` / `•` prefixes, reasoning blocks as collapsible `[thinking...]`.
- **Thread list:** Horizontal tab bar; sessions managed via slash commands (see Phase 5b).

See [Phase 5a implementation notes](../development/phase_5a/implemented.md).

---

## Phase 5b — Slash commands and named sessions — Done

**Goal:** Local slash commands for session management and quick actions.

**Delivered:**

- **Slash commands:** `/help`, `/clear`, `/compact [keep]`, `/new`, `/rename <name>`, `/session <id|index|name>`, `/sessions`, `/skill <name>` (backend-handled).
- **Inline autocomplete:** When typing `/`, suggestions appear with command name and description.
- **Named sessions:** Rename via `/rename` or thread tab dropdown.

See [Phase 5b implementation notes](../development/phase_5b/implemented.md) and [Slash commands](commands.md).

---

## Phase 8 — Research tools — Done

**Goal:** Enable the assistant to search the web, fetch URL content, and discover custom node packages and example workflows.

**Delivered:**

- **webSearch** — Search the web for ComfyUI resources, tutorials, workflows (SearXNG or DuckDuckGo).
- **fetchWebContent** — Fetch and extract content from a URL; detect embedded workflows.
- **searchNodeRegistry** — Search the ComfyUI Registry for custom node packages.
- **getExampleWorkflow** — Fetch example workflows extracted from ComfyUI_examples by category.
- **API endpoints:** `/api/research/search`, `/api/research/fetch`, `/api/research/registry`, `/api/research/examples`.

See [Phase 8 implementation notes](../development/phase_8/implemented.md).

---

## Phase 5 — Polish and non-functional requirements — Planned

**Goal:** Harden installability, configurability, security, and usability.

**Planned deliverables:**

- **Installability** — Reliable install via ComfyUI Manager; clear manual install and build docs.
- **Configurability** — UI or settings to add and edit **multiple LLM providers** (name, URL, API key, model); secrets from env or secure config.
- **Security** — Harden back agent (read-only outside workspace; safe handling of third-party custom node content); document assumptions.
- **Usability** — Multi-language support (responses and UI in the user’s language); optional language selector or detection.
- **Context and performance** — Keep documentation on demand; optional embeddings for user context if available.
- **Compatibility** — Document tool/skill contracts; state supported ComfyUI versions; maintain a CHANGELOG for breaking changes.

**Success criteria (target):** Install via Manager, configure several providers from the UI, use the assistant in your language, with security documented and no regression on earlier phases.

---

## Order and dependencies

- **Phases 1 → 2 → 3 → 4** are sequential: each builds on the previous.
- **Phase 5a, 5b** (UI polish, slash commands) are done; **Phase 5** (Manager, multi-provider UI, i18n, security) is planned.
- **Phase 8** (research tools) is independent and done.

Each phase is designed to be **shippable** on its own (e.g. “Phase 1 release” = MVP + user context and manual skills).

---

## More detail

- Implementation notes for completed phases: [development/](../development/) (e.g. `phase_0/implemented.md`, `phase_3/implemented.md`, `phase_4/implemented.md`, `phase_5a/implemented.md`, `phase_5b/implemented.md`, `phase_8/implemented.md`).
- Full phase definitions and success criteria: [planning/comfyui_assistant_development_phases.md](../planning/comfyui_assistant_development_phases.md).
