# ComfyUI Assistant — Base skills (planning)

This document plans the **base skills** the agent needs to be a powerful tool: knowledge of ComfyUI, diffusion models, nodes and workflows, plus the ability to research and stay up to date. The concrete definition of each skill (skills table, tools) is in [comfyui_assistant_skills.md](comfyui_assistant_skills.md).

---

## 1. Current situation

ComfyUI Assistant today can:

- Perform basic actions: add/remove nodes and execute workflows.
- Analyze installed nodes and reason about their use.
- Create simple and complex workflows (simpler ones with better results).
- Answer questions about workflows and configured values.

These capabilities give it strong potential, but **we depend on the model**: in testing (e.g. Grok, GPT-5.2) the model lacks sufficient knowledge about diffusion models, architectures (e.g. confusing SD with “Z-Image” or anime) and specific nodes (e.g. FaceDetailer), and fails on connections or parameters even when the intent is correct.

---

## 2. Goal

For the assistant to be truly powerful it needs:

1. **Knowledge** of models, workflows and nodes (what they are, typical parameters, how they combine).
2. **Analysis** of the user’s request and **generation** of coherent workflows from that knowledge.
3. **Updating**: ability to incorporate new models, workflows and nodes (same principles, different documentation).

---

## 3. Options considered

| Option | Description |
|--------|-------------|
| **1** | The model researches on its own and feeds back (search and content-consumption tools). |
| **2** | Provide a curated knowledge base (skills + documentation) for the model to use in context. |
| **3** | Fine-tune a model with all the required knowledge. |

**Option 3** is ruled out at this stage (cost and scope). **Options 1 and 2** are complementary and are combined in the approach below.

---

## 4. Proposed approach

### 4.1 Strategy 1 — Research and self-service (Phase 1)

Give the agent **tools** to research and consume external content:

- **1.a — Web search**  
  - Search the web for documentation on nodes, models and workflows.  
  - Consume links (Reddit, Gist, X, etc.) where a workflow is shared: fetch the JSON/workflow and analyze it.

- **1.b — Node registry search**  
  - Search the ComfyUI registry (or equivalent) for nodes that match the user’s requirement (by name, category, description).

- **1.c — Skills from research**  
  - From 1.a and 1.b, the assistant can suggest creating **user skills** (stored in `user_context/skills/`) with what was learned in that session.

Outcome: the agent can discover nodes, documentation and workflows on its own and persist knowledge in user context.

### 4.2 Strategy 2 — Curated knowledge base (Phase 2)

Create **base skills** that inject stable, well-structured knowledge:

- **2.a — Skill content**
  - **ComfyUI**: official docs, built-in (OOB) nodes, base workflows and API (e.g. ComfyUI docs tutorial as initial set).
  - **Models**: most popular supported models, architecture, optimal inference parameters, typical workflows.
  - **Nodes**: most used nodes, how to use them, combinations and use cases.

- **2.b — Tools to generate skills**
  - Tools (or pipelines) to generate/update the skills in 2.a automatically from sources (docs, node lists, examples).

Phase 2 requires **prior definition**: which exact skills, which nodes, which models and which workflows to include. It can be split into:
- Define the inventory (skills, nodes, models, workflows).
- Implement the automatic skill-generation tool.
- Generate and maintain the skills with that tool.

---

## 5. Implementation plan

| Phase | Scope | Deliverables |
|-------|--------|--------------|
| **Phase 1** | Strategy 1 | Web search tool (1.a); node registry search tool (1.b); flow for the assistant to suggest creating user skills from research (1.c). |
| **Phase 2** | Strategy 2 | Definition (inventory of skills/nodes/models/workflows); tool to create/update skills automatically; base skills generated and maintained. |

Phase 2 depends on that definition; until then, curated skills and the generation tool are not implemented.

---

## 6. Relation to other documents

- **Concrete skills (base, user, custom node)** and associated tools: [comfyui_assistant_skills.md](comfyui_assistant_skills.md).
- **System skills** (injected prompt): `system_context/skills/` (01_base_tools, 02_tool_guidelines, 03_node_reference, 04_environment_tools, 05_workflow_execution).
- **Project context**: `.agents/project-context.md`.
