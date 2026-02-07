# ComfyUI Assistant — tools

This document lists **tools**: the actions that skills (or the agent) can run. Tools are split by **which agent** uses them: **UI agent** (frontend) vs **back agent** (backend). Naming convention: UI tools use camelCase and run in the frontend via `window.app` where applicable; back tools are backend-only and may use camelCase or snake_case for consistency with the backend.

See [desired skills](comfyui_assistant_skills.md) for how tools are used by skills.

---

## UI agent tools

Tools available to the agent running in the frontend. They have access to the graph via `window.app` (and, when implemented, to context provided by the back agent via .agents/).

### Currently implemented

Defined in `ui/src/tools/` and `tools_definitions.py`; executed in the frontend.

| Tool | Description | Main parameters |
|------|-------------|-----------------|
| **addNode** | Adds a new node to the ComfyUI workflow. Allows specifying the node type and optionally its position on the canvas. | `nodeType` (string), `position` (optional `{ x, y }`) |
| **removeNode** | Removes an existing node from the ComfyUI workflow by its ID. | `nodeId` (number) |
| **connectNodes** | Connects two nodes. Creates a connection from an output slot of one node to an input slot of another. | `sourceNodeId`, `sourceSlot`, `targetNodeId`, `targetSlot` (numbers) |
| **getWorkflowInfo** | Gets information about the current workflow: list of nodes, connections, and general configuration. | `includeNodeDetails` (optional boolean) |

### Planned (UI agent)

- **refresh_environment** — Asks the back agent to rescan the ComfyUI installation (custom_nodes/, models/) and update the shared context in .agents/. The UI agent uses this when it does not have enough context to perform a task, or after a **failure** that suggests the environment changed (e.g. the user asks to use "VHS Video Combine", the agent tries to add it, validation fails because the node is not found; the agent invokes refresh_environment, discovers the node was uninstalled, then tells the user that the node is required and is missing).
- **read_documentation** — Fetches documentation **on demand** (ComfyUI or custom node docs, e.g. from .agents/ or a docs source) and returns relevant excerpts. Context size is limited, so we only inject the documentation that is needed for the current request rather than loading everything up front.
- **setNodeWidgetValue** — Sets the value of a widget on an existing node (e.g. steps, cfg, seed on a KSampler; prompt text on a CLIPTextEncode). Required for configuring nodes after creation and for applying user rules (e.g. filling a prompt node with generated text). Parameters: nodeId, widget name or index, value (type depends on widget).
- **fillPromptNode** — Fills a prompt node (e.g. CLIPTextEncode) with the given text. This is the tool that applies a **generated prompt** (from a skill) to a specific node. May be implemented as a thin wrapper over setNodeWidgetValue for the "text" widget of prompt nodes.
- **create_skill** — Requests creation (or update) of a user skill. The UI agent invokes it with skill name, description, and content/instructions when the user asks to remember a preference or when the assistant suggests saving a procedure as a skill. The request is fulfilled by the back agent (persist to .agents/skills/ or user context).

**Prompt generation:** Generating prompts (detailed image prompt, tag-based image prompt, video prompts, etc.) using a **guide** is a **skill**, not a tool. The LLM (or a dedicated skill) produces the prompt text; the **tool** that writes that text into the workflow is **fillPromptNode** (or setNodeWidgetValue).

---

## Back agent tools (actions)

Actions or "tools" that only the **back agent** can run. They have access to the filesystem (custom_nodes/, models/) and to the ComfyUI API (e.g. to apply a full workflow). Results are written into .agents/ or returned to the UI agent via the shared layer.

- **refresh_environment** (triggered by UI) — Scan `custom_nodes/` and `models/`, optionally read each custom node's .agents/ and .agents/skills/, build the environment context (installed node types, available models, merged docs), and write it into .agents/ for the UI agent to use. Invoked when the UI agent calls the UI tool `refresh_environment`.
- **read_documentation** (on demand) — When the UI agent needs documentation for a specific node or topic, the back can resolve it (from .agents/ of installed nodes or from curated docs) and return only the relevant excerpt, so context stays bounded.
- **apply_workflow_json** — Receives a workflow representation (e.g. JSON compatible with ComfyUI API), applies it via the ComfyUI API (e.g. replace or load the graph). Used when the UI agent delegates "build and apply this complex workflow" to the back agent.
- **execute_workflow** — Triggers execution of the current (or a given) workflow via the ComfyUI API (e.g. queue). Implemented by the back agent but with **feedback to the UI**: progress updates, completion status, errors, and optionally output previews (e.g. image/video URLs or thumbnails) so the agent and the user can see that the run finished and what was produced.
- **search_installed_custom_nodes** — Search within the **installed** custom nodes (by name or capability) and return matches. Result can be written to .agents/ or returned to the UI so the agent can suggest or use the right node.
- **search_documented_custom_nodes** — Search within the set of custom nodes for which we have **documentation** (e.g. .agents/skills we maintain for popular nodes). Enables "find a node that does X" even if the user has not installed it yet. We will make an effort to document the most popular nodes if such documentation does not already exist.
- **create_skill** (triggered by UI) — Persists a user skill: writes the skill definition (name, description, instructions) to the workspace (e.g. .agents/skills/) or user context store. Invoked when the UI agent calls the UI tool `create_skill`. Ensures the new skill is available in subsequent sessions.

---

## Summary

| Concept | UI agent | Back agent |
|--------|----------|------------|
| Graph (add/remove/connect) | addNode, removeNode, connectNodes | — |
| Workflow state | getWorkflowInfo | — |
| Environment / installed | refresh_environment (triggers back), reads .agents/ | refresh_environment (scan + write .agents/) |
| Documentation | read_documentation (request) | read_documentation (resolve + return) |
| Node config | setNodeWidgetValue, fillPromptNode | — |
| Complex workflow | — | apply_workflow_json |
| Execute / run workflow | — | execute_workflow (with feedback to UI) |
| Search nodes | — | search_installed_custom_nodes, search_documented_custom_nodes |
| Create / save skill | create_skill (request) | create_skill (persist to .agents/skills/ or user context) |

Prompt **generation** (with a guide) = **skill**. Prompt **application** to a node = **tool** (fillPromptNode / setNodeWidgetValue).
