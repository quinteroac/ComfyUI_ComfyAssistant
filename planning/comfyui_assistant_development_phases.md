# ComfyUI Assistant — development phases

This document defines a **phased development plan** from the current MVP to the full vision described in [features](comfyui_assistant_features.md), [design](comfyui_assistant_design.md), [tools](comfyui_assistant_tools.md), [skills](comfyui_assistant_skills.md), [base skills planning](comfyui_assistant_base_skills.md), and [non-functional requirements](comfyui_assistant_non_functional_features.md). Each phase delivers a usable increment and sets the base for the next. Phases 8–9 implement the base-skills strategy; former Phase 6–7 are renumbered to Phase 10–11 and deprioritized after them.

---

## Phase 0 — Current MVP (baseline)

**Goal:** Establish the minimal assistant: chat + graph manipulation with no backend agent and no persistent context.

**Delivered:**

- **UI:** Chat interface (threads, messages, markdown, attachments).
- **LLM:** OpenAI-compatible API (env: `OPENAI_API_BASE_URL`, API key, model). Multi-provider via base URL.
- **Tools (UI, implemented):** `addNode`, `removeNode`, `connectNodes`, `getWorkflowInfo`. Execution via frontend (`window.app`); backend streams LLM response and tool definitions.
- **Prompts:** System message in `agent_prompts.py`; tool definitions in `tools_definitions.py` and `__init__.py`.
- **No back agent**, no `.agents/` shared context, no scan of `custom_nodes/` or `models/`, no persistent user context, no skill creation.

**Out of scope for Phase 0:** Environment awareness, documentation on demand, node configuration (widgets), user skills, workflow execution, apply_workflow_json.

---

## Phase 1 — User context and skills (manual)

**Goal:** Persist **user context** (rules, preferences, narrative) and support **manually created** user skills. Optional first-time onboarding. No back agent yet — skills are created by the user (e.g. by adding files to the workspace), not by an agent tool.

**Deliverables:**

1. **Structured user context (SQLite or equivalent)** — Store user-defined rules (e.g. "always use Preview Image instead of Save Image") and preferences in a queryable form. Location: assistant workspace (e.g. under the custom node). Used when applying workflow changes.
2. **File-based narrative and skills** — SOUL.md / goals.md and a `skills/` folder (e.g. under .agents/) with one .md per user skill. LLM reads these for personality and "how to behave." Skills are **created and edited manually** by the user (add/edit files in the workspace). The agent uses them but does not create them in this phase.
3. **Load user context into prompts** — When building the system or context for the UI agent, inject relevant rules and skill summaries (or full skill text if small) so the agent applies user preferences and uses the manually created skills.
4. **Optional: First-time onboarding** — Short flow: agent asks for personality and a few questions (goals, experience level); answers persisted to SOUL.md / goals.md and structured store. Can be skipped with neutral defaults.

**Success criteria:** User adds a skill file (or rule in the structured store) e.g. "always use Preview Image instead of Save Image"; on later turns the agent applies it. User can ask "what did I ask you to remember?" and agent reflects stored context (rules + skills from the workspace).

**Dependencies:** Phase 0. Persistence is done by the existing backend writing to the extension workspace. **create_skill** (agent-driven skill creation) is deferred to Phase 3, when the back agent exists.

**Implementation (Phase 1):** Workspace layout and skill file convention are documented in `.agents/project-context.md` (User context workspace). Phase 3 (create_skill) will persist to the same `user_context/skills/` layout.

---

## Phase 2 — Node configuration and prompt application

**Goal:** Let the agent not only add and connect nodes but also **configure** them (widgets) and **set prompt text** in prompt nodes. No back agent yet.

**Deliverables:**

1. **setNodeWidgetValue** — New UI tool: set a widget value on an existing node (e.g. steps, cfg, seed on KSampler; any widget by name or index). Parameters: `nodeId`, widget identifier, `value`. Implementation in `ui/src/tools/` and backend tool definition.
2. **fillPromptNode** — New UI tool: set the text of a prompt node (e.g. CLIPTextEncode). Parameters: `nodeId`, `text`. Can be implemented as a wrapper over setNodeWidgetValue for the text widget.
3. **Prompts:** Update system prompt so the agent knows when to use these tools (e.g. "after adding a KSampler, set steps to 20"; "put the user's prompt in the CLIPTextEncode node"). User context from Phase 1 (e.g. rules) is already available when applying workflow changes.
4. **Optional:** Prompt-generation guidance in the system prompt (e.g. short guide for "detailed image prompt" or "tag-based prompt") so the agent can generate better prompt text before calling fillPromptNode. This is skill-in-prompt only; no separate skill store beyond Phase 1.

**Success criteria:** User can say "create a txt2img workflow with 20 steps and prompt 'a cat'" and the agent adds nodes, connects them, sets steps, and fills the prompt node.

**Dependencies:** Phase 0, Phase 1. No new backend services beyond Phase 1.

---

## Phase 3 — Back agent and environment awareness

**Goal:** Introduce a **back agent** (or backend process) that scans the ComfyUI installation and exposes context to the UI agent via a shared **.agents/** layer. Enable **refresh_environment** and **read_documentation** on demand. **Integrate skills with the back agent:** add **create_skill** so the agent can create and persist user skills (Phase 1 had manual skills only).

**Deliverables:**

1. **.agents/ shared layer** — Define layout: e.g. `.agents/context/` (or equivalent) for environment context written by the back. UI agent (or backend when building messages) reads this context when needed. Document the contract (what the back writes, what the UI expects).
2. **Back agent / backend scanner** — Process or endpoint that:
   - Scans `custom_nodes/` and `models/` (and optionally each custom node's `.agents/` and `.agents/skills/`).
   - Builds a structured context (installed node types, available models, merged doc excerpts).
   - Writes result into `.agents/` (e.g. JSON or markdown). Respect security: read-only outside workspace; do not execute untrusted code from custom nodes.
3. **refresh_environment** — UI tool that triggers the back scan and waits for updated context (or polls). After a failure (e.g. "node type not found"), the agent can call refresh_environment, re-read context, and inform the user (e.g. "that node was uninstalled").
4. **read_documentation** — UI tool that requests documentation for a given node or topic. Backend resolves it (from .agents/ of installed nodes or curated docs) and returns only the relevant excerpt (on demand, to limit context size).
5. **search_installed_custom_nodes** and **search_documented_custom_nodes** — Implemented in the back; results written to .agents/ or returned to the UI so the agent can suggest nodes and "do you have X installed?" flows.
6. **create_skill (integrated with back agent)** — UI tool: name, description, instructions. Back agent receives the payload and writes safely into the workspace (e.g. new file in .agents/skills/ or user skill store). From this phase onward the agent can create and persist user skills when the user asks to "remember" something or when the assistant suggests saving a procedure.
7. **Prompts:** System prompt (or context injection) includes how to use refresh_environment when context is missing or after a failure, when to call read_documentation, and when to use create_skill.

**Success criteria:** User asks "what custom nodes do I have?" or "how do I use ADetailer?"; agent uses refreshed context and/or read_documentation and answers correctly. If the user asks for a node that is not installed, agent can explain and suggest installation. User says "remember to always use Preview Image instead of Save Image"; agent creates a skill via create_skill and on later turns applies it.

**Dependencies:** Phase 2. Requires backend component that can read the ComfyUI installation (same process as ComfyUI or separate service that has access to the paths).

---

## Phase 4 — Workflow execution and complex workflows

**Goal:** Support **execute_workflow** (run the graph, with feedback to the UI) and **apply_workflow_json** (build and load a full workflow via the back). Enables "run this" and "build this whole workflow for me."

**Deliverables:**

1. **execute_workflow** — Back agent (or backend) triggers execution of the current workflow via ComfyUI API (queue). Stream or push **feedback to the UI**: progress, completion, errors, and optionally output previews (e.g. image/video URLs). UI agent can then "run workflow and report result" to the user.
2. **apply_workflow_json** — Back agent accepts a workflow representation (JSON compatible with ComfyUI API), applies it (e.g. load graph via API), and writes status/result to .agents/ or returns to UI. UI agent delegates "build and apply this workflow" when the task is complex.
3. **Prompts:** System prompt describes when to delegate to the back for execution or full workflow apply, and how to interpret progress/result for the user.

**Success criteria:** User says "run the workflow" and gets progress and a short result summary (and optionally sees outputs). User says "create a full img2img workflow with upscale" and the back can build and load it in one go.

**Dependencies:** Phase 3 (back agent, .agents/). ComfyUI API for queue and graph load must be available and documented.

---

## Phase 5a — Bottom panel + terminal aesthetic (DONE)

**Goal:** Move the assistant from a sidebar tab to a **bottom panel** (like ComfyUI's Console) with a terminal/console-style UI aesthetic. See [UI design](comfyui_assitant_ui_design.md).

**Delivered:**

1. **Layout and placement** — Assistant registers as a `bottomPanelTabs` entry (with sidebar fallback code). Panel opens at the bottom of the ComfyUI UI.
2. **Terminal aesthetic** — Monospace font (JetBrains Mono stack), 13px, compact spacing, no chat bubbles, green `>` prompt prefix for user messages, `comfy>` prompt in composer.
3. **First impression** — ASCII ComfyUI logo + "Type a message or /help to get started".
4. **Thread list** — Horizontal tab bar instead of vertical list.
5. **CSS consolidation** — Merged `assistant-ui-theme.css` + `chat-styles.css` into `terminal-theme.css`. Fixed root ID mismatch bug (`#comfyui-react-example-root` → `#comfyui-assistant-root`).

---

## Phase 5b — Slash commands and sessions (DONE)

**Goal:** Add slash commands, named sessions, and integrated configuration to the terminal UI.

**Delivered:**

1. **Slash commands (`/`)** — Commands invokable via `/` prefix: `/help`, `/clear`, `/new`, `/rename <name>`, `/sessions`. Inline autocomplete when typing `/`.
2. **Sessions** — Threads can be **named** via `/rename` or via the Rename option in the thread tab dropdown; `/sessions` lists all; `/new` creates and switches.
3. **`/help`** — Shows available commands in a markdown table.
4. **Rename in thread list** — "Rename" menu item in the thread tab's ⋮ dropdown (via `window.prompt()`).

**Deferred to later:**
- `/settings` (configuration entry points)
- First-time configuration flow
- Media and attachments (Phase 5 later sub-phase)

**Success criteria (met):** User can use `/help`, `/clear`, `/new`, `/rename`, `/sessions`; named sessions via command or dropdown; autocomplete when typing `/`.

**Dependencies:** Phase 5a.

---

## Phase 8 — Research and self-service (base skills, Strategy 1)

**Goal:** Give the agent **tools** to research and consume external content so it can discover nodes, documentation and workflows on its own and persist knowledge in user context. See [base skills planning](comfyui_assistant_base_skills.md).

**Deliverables:**

1. **Web search tool** — Search the web for documentation on nodes, models and workflows. Consume links (Reddit, Gist, X, etc.) where a workflow is shared: fetch the JSON/workflow and analyze it.
2. **Node registry search tool** — Search the ComfyUI registry (or equivalent) for nodes that match the user’s requirement (by name, category, description).
3. **Skills from research** — Flow for the assistant to suggest creating **user skills** (stored in `user_context/skills/`) from what was learned in a session using the above tools (create_skill from Phase 3 is used for persistence).

**Success criteria:** Agent can search for node/workflow documentation and shared workflows, search the node registry for suggestions, and offer to save findings as user skills.

**Dependencies:** Phase 3 (create_skill, user context). Optional: Phase 4 if workflow ingestion from links requires apply_workflow_json.

---

## Phase 9 — Curated knowledge base (base skills, Strategy 2)

**Goal:** Create **base skills** that inject stable, well-structured knowledge (ComfyUI, models, nodes) and provide tooling to generate/update them automatically. See [base skills planning](comfyui_assistant_base_skills.md).

**Deliverables:**

1. **Definition** — Inventory of which skills to create, which nodes, which models and which workflows to include (document in planning or `.agents/`).
2. **Skill content** — Base skills covering: **ComfyUI** (official docs, OOB nodes, base workflows and API, e.g. ComfyUI docs tutorial); **models** (popular supported models, architecture, optimal inference parameters, typical workflows); **nodes** (most used nodes, how to use them, combinations and use cases).
3. **Tool to generate skills** — Tool or pipeline to generate/update these base skills automatically from sources (docs, node lists, examples).
4. **Generated and maintained base skills** — Produce and maintain the skills using the above tool; inject them via system_context or documented injection path.

**Success criteria:** Agent has access to curated ComfyUI/model/node knowledge; skills can be regenerated when sources change.

**Dependencies:** Phase 8 recommended (informed by research tooling). Phase 3 (environment, docs). Phase 9 depends on prior definition; until the inventory is defined, curated skills and the generation tool are not implemented.

---

## Phase 10 — Polish and non-functional requirements

*(Previously Phase 6. Lower priority than Phase 8–9; see [base skills](comfyui_assistant_base_skills.md).)*

**Goal:** Harden **installability**, **configurability**, **security**, and **usability** to meet the [non-functional requirements](comfyui_assistant_non_functional_features.md) document.

**Deliverables:**

1. **Installability** — Ensure the node is **installable via ComfyUI Manager** (correct `pyproject.toml` / manifest, build artifacts in dist/). Document manual install and build steps. No mandatory external sign-up at install time.
2. **Configurability** — **UI or settings** to add and edit **multiple LLM providers** (name, base URL, API key, model). All providers used via OpenAI-compatible API. Secrets from env or secure config, not hardcoded.
3. **Security** — Harden back agent: read-only outside workspace; **sanitize or constrain** content from third-party custom nodes' `.agents/` before injecting into context; minimal read. Document security assumptions.
4. **Usability** — **Multi-language:** respect user language for responses and generated UI text. Optional: language selector or detection from first message.
5. **Context and performance** — Confirm documentation remains on demand; optional **embeddings** layer for user context when API is available; otherwise fixed window or summary as in design.
6. **Compatibility and maintainability** — Document **tool and skill contracts**; state supported ComfyUI version range; keep a CHANGELOG for breaking changes.

**Success criteria:** User can install via Manager, add several LLM providers from the UI, use the assistant in their language, and security notes are documented. No regression on Phase 1–5 and 8–9 behavior.

**Dependencies:** Phases 1–5, 8–9. Can be parallelized (e.g. Manager metadata early; security review before or after Phase 4).

---

## Phase 11 — Risk mitigation (post–Phase 3 review)

*(Previously Phase 7. Lower priority than Phase 8–9.)*

**Goal:** Address risks identified in the Phase 3 PR review (e.g. Bugbot — Medium Risk): new backend APIs, background scanning, prompt injection (environment summary), and the `@assistant-ui/react-ai-sdk` tool-call patch. Document and, where applicable, implement mitigations so the model’s context and tool execution remain bounded and maintainable.

**Deliverables:**

1. **Risks document** — `development/phase_6/risks_from_phase_3.md`: four risk areas (APIs, background scan, prompt injection, patch) with concrete mitigations and checklists.
2. **Backend APIs** — Confirm Phase 3 endpoints follow the same access policy as the rest of the backend; document route list and assumptions (e.g. same origin, no new public exposure).
3. **Background scanning** — Ensure scan failure does not block startup; optional: make auto-scan configurable; define or enforce limits (scan duration, cache/summary size).
4. **Prompt injection** — Document that the environment summary is from our controlled cache (not raw user input); keep or define a strict size limit for the injected summary; document in security/context docs.
5. **Patch to assistant-ui** — Document in `ui/patches/` what the patch fixes (streamed tool-call execution and result return) and what it does not change; add a note for future upgrades (re-apply or re-evaluate patch, smoke test tool execution).

**Success criteria:** All four risk areas documented with mitigations applied or explicitly accepted. At minimum: route assumptions documented; environment summary size bounded and documented; patch purpose and upgrade plan documented. No regression in Phase 3 behaviour.

**Dependencies:** Phase 3 done. Can be done after or in parallel with Phase 4/5/8/9/10.

**Reference:** [development/phase_6/risks_from_phase_3.md](../development/phase_6/risks_from_phase_3.md) for the detailed checklist.

---

## Summary table

| Phase | Focus | Key deliverables |
|-------|--------|-------------------|
| **0** | MVP (current) | Chat, 4 graph tools, getWorkflowInfo, OpenAI-compatible LLM |
| **1** | User context & skills (manual) | SQLite + file-based skills (user-created), load context into prompts, optional onboarding |
| **2** | Node config & prompts | setNodeWidgetValue, fillPromptNode, prompt guidance in system prompt |
| **3** | Back agent & environment | .agents/ layer, refresh_environment, read_documentation, search_installed/documented_custom_nodes, **create_skill** (integrated with back) |
| **4** | Execution & complex workflows | execute_workflow (with UI feedback), apply_workflow_json |
| **5a** | Terminal-style UI (done) | Bottom panel, terminal aesthetic, ASCII logo + welcome, horizontal thread tabs, CSS consolidation |
| **5b** | Slash commands & sessions (done) | `/help`, `/clear`, `/new`, `/rename`, `/sessions`; autocomplete; Rename in thread dropdown |
| **8** | Research & self-service (base skills) | Web search tool, node registry search tool, flow to suggest user skills from research |
| **9** | Curated knowledge base (base skills) | Definition (inventory), base skill content (ComfyUI/models/nodes), tool to generate skills, generated skills |
| **10** | NFRs & polish | ComfyUI Manager install, multi-provider config UI, security, multi-language, docs |
| **11** | Risk mitigation (post–Phase 3) | Document and mitigate Phase 3 risks: APIs, scan, prompt injection, assistant-ui patch |

---

## Notes

- **Order:** Phases 1 → 2 → 3 → 4 are sequential by dependency. Phase 5 (terminal UI) depends on Phase 0 and can be developed in parallel with or after Phase 1–4. **Phase 8 (research/self-service) and Phase 9 (curated knowledge base)** follow Phase 5b and are prioritized before Phase 10–11. Phase 10 (NFRs & polish) depends on Phases 1–5 and 8–9. Phase 11 (risk mitigation) depends on Phase 3 and can run after or in parallel with Phase 4/5/8/9/10.
- **Scope per phase:** Each phase should be shippable (e.g. "Phase 1 release" = MVP + user context and manually created skills). Avoid moving to the next phase until the current one is stable and tested. Agent-driven **create_skill** is delivered in Phase 3 with the back agent.
- **References:** For base skills rationale and strategy, see [comfyui_assistant_base_skills.md](comfyui_assistant_base_skills.md). For detailed tool/skill behavior, see [comfyui_assistant_tools.md](comfyui_assistant_tools.md) and [comfyui_assistant_skills.md](comfyui_assistant_skills.md). For architecture and security, see [comfyui_assistant_design.md](comfyui_assistant_design.md) and [comfyui_assistant_non_functional_features.md](comfyui_assistant_non_functional_features.md).