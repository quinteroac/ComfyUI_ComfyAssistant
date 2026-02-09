# Roadmap

This document summarizes the development roadmap for ComfyUI Assistant. The project is built in **phases**: each phase delivers a working increment and sets the base for the next.

**Status overview**

| Phase | Status   | Focus |
|-------|----------|--------|
| **0** | Done     | MVP: chat + graph tools |
| **1** | Done     | User context and manual skills |
| **2** | Done     | Node configuration and prompts |
| **3** | Done     | Environment awareness, search, create_skill |
| **4** | Planned  | Workflow execution and complex workflows |
| **5** | Planned  | Polish and non-functional requirements |

---

## Phase 0 — MVP (baseline) — Done

**Goal:** Minimal assistant: chat and graph manipulation, no persistent context.

**Delivered:**

- Chat UI (threads, messages, markdown).
- OpenAI-compatible LLM (Groq or any provider via `.env`).
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

## Phase 4 — Workflow execution and complex workflows — Planned

**Goal:** Run the workflow from the assistant and load full workflows from a description or JSON.

**Planned deliverables:**

- **execute_workflow** — Trigger execution of the current graph via ComfyUI (queue), with progress and result feedback in the UI.
- **apply_workflow_json** — Build and load a full workflow (JSON) in one go for complex setups.
- System prompt updates so the assistant knows when to run the workflow or apply a full workflow and how to report results.

**Success criteria (target):** You say “run the workflow” and get progress and a result summary. You ask for “a full img2img workflow with upscale” and the system can build and load it.

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
- **Phase 5** can be started in parallel (e.g. Manager metadata, i18n) and finalized after Phase 4.

Each phase is designed to be **shippable** on its own (e.g. “Phase 1 release” = MVP + user context and manual skills).

---

## More detail

- Implementation notes for completed phases: [development/](../development/) (e.g. `phase_0/implemented.md`, `phase_1/implemented.md`, `phase_2/implemented.md`, `phase_3/implemented.md`).
- Full phase definitions and success criteria: [planning/comfyui_assistant_development_phases.md](../planning/comfyui_assistant_development_phases.md).
