# ComfyUI Assistant — desired skills

This document is for **ideation** and references [ComfyUI Assistant design](comfyui_assistant_design.md).

Skills needed by the agent can be grouped as follows:

- **Base skills** — Core skills: everything related to creating workflows, knowledge of the ComfyUI environment, ComfyUI documentation, and built-in (OOB) nodes.
- **User skills** — Skills derived from user context. They are created by the user according to their preferences; the assistant can suggest creating a skill.
- **Custom node skills** — Skills for using custom nodes: from documentation on how to use them to specific actions (e.g. Impact Pack could have a skill “create inference workflow with ADetailer”).

Skills rely on **tools** and other skills. Tools are defined in [comfyui_assistant_tools.md](comfyui_assistant_tools.md).

---

## Base skills

| Skill | Tools | Notes |
|-------|--------|--------|
| **Analyze workflow** | getWorkflowInfo, read_documentation | Understand current graph: nodes, connections, types; request doc only when needed. |
| **Create or modify workflow (graph)** | addNode, removeNode, connectNodes, getWorkflowInfo | Add/remove nodes and links; build or adjust workflow structure. |
| **Configure node parameters** | setNodeWidgetValue | Set widget values on a node (steps, cfg, seed, etc.) without changing the graph. |
| **Apply prompt to node** | fillPromptNode (or setNodeWidgetValue) | Write generated or user prompt text into a prompt node (e.g. CLIPTextEncode). |
| **Ensure environment context** | refresh_environment, context in .agents/ | Decide when to refresh (missing context or after failure); invoke refresh and use result to know what is installed. |
| **Find nodes (installed or documented)** | search_installed_custom_nodes, search_documented_custom_nodes (via back), read_documentation | Search by name or capability; distinguish installed vs documented; suggest installation if needed. |
| **Use documentation on demand** | read_documentation | Request only the doc needed for the current task (ComfyUI OOB or custom nodes) to avoid filling context. |
| **Run workflow and report result** | execute_workflow (back, feedback to UI) | Trigger execution, interpret progress and outcome, explain result (and optionally previews) to the user. |
| **Apply full workflow from back** | apply_workflow_json (back) | Delegate building a full workflow to the back agent and load it into ComfyUI. |
| **Generate prompts (by type)** | — (output → fillPromptNode via Apply prompt to node) | Generate prompt text using a guide: detailed image, tag-based image, video, etc. These are skills, not tools; the text is applied with **Apply prompt to node**. |
| **ComfyUI OOB nodes documentation** | read_documentation | Use **Use documentation on demand** when the topic is ComfyUI built-in nodes. |
| **Create skill** | create_skill | Create or update a user skill: when the user asks to remember a preference or procedure, or when the assistant suggests saving one, invoke create_skill with name, description, and instructions so it is persisted (e.g. in .agents/skills/) and available later. |

---

## User skills

Skills derived from user context: preferences, recurring procedures, or rules the user wants the assistant to follow. They are created via the base skill **Create skill** (tool: create_skill)—either when the user asks to remember something or when the assistant suggests saving a procedure for next time. The rest is defined **with the user** per their preferences and context.

---

## Custom node skills

Skills for using specific custom nodes: from documentation on usage to concrete workflows (e.g. Impact Pack → “create inference workflow with ADetailer”). They build on **base skills**: Use documentation on demand, Find nodes (installed or documented), Create or modify workflow, Configure node parameters, Apply prompt to node.

| Skill | Tools | Ref skill |
|-------|--------|-----------|
| Custom node documentation | read_documentation | Use documentation on demand |
