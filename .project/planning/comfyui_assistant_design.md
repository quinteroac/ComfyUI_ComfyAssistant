# ComfyUI Assistant — design ideation

This document is for **design ideation only**, not implementation.

Based on the capabilities defined in the [features](comfyui_assistant_features.md) doc, there are three main problems to solve:

1. **User context**
2. **Awareness of the user’s ComfyUI environment**
3. **Knowledge of the ComfyUI ecosystem** (built-in and custom nodes)

The design assumes **two agents** that cooperate via a shared **.agents/** layer (see *Architecture* below).

---

## Architecture: two agents

- **UI agent (front)** — Runs in the frontend. Talks to the user, has access to the graph via tools (add/remove/connect node, read workflow). It does **not** have access to the ComfyUI installation filesystem. When it needs something only the backend can do (e.g. list installed nodes, build a complex workflow), it **delegates** to the back agent.
- **Back agent** — Runs in the backend. Has access to the filesystem (e.g. `custom_nodes/`, `models/`). It **obeys** the UI agent: it performs tasks on request (e.g. “list installed nodes”, “build and apply this workflow”) and writes results or updated context into **.agents/** so the UI agent can use them.
- **Communication** — The two agents coordinate via **.agents/**: the back agent updates context there (e.g. installed nodes, models, preprocessed `.agents/` from custom nodes); the UI agent (and the back agent when needed) reads that context. Requests from UI to back and responses from back to UI flow through this shared layer (or a dedicated channel that updates .agents/ as needed).

**Example flows:**

- User: “What custom nodes do I have installed?” → UI agent: “I need installed nodes but I don’t have access; I ask the back.” → Back triggers back agent → Back agent: scans `custom_nodes/`, writes result into .agents/, signals done → Back returns to UI → UI agent: “These are your installed nodes.”
- Next turn, user: “How can I do ADetailer?” → UI agent: “I check what nodes the user has for ADetailer; I ask the back if needed.” → Back: “Context already has installed nodes; here they are.” → UI agent: “You can use Impact Pack nodes.”
- User asks for a complex workflow → UI agent **delegates** “build and apply this workflow” to the back agent → Back agent builds the graph (e.g. as JSON), applies it via the ComfyUI API, writes status/result into .agents/ → UI agent informs the user.

---

## 1. User context

User context is implemented as a **single combined solution** with three layers. The assistant’s **workspace** under the custom node is the only place the assistant may write (see *Security* in section 2).

### 1.1 Structured store (SQLite or equivalent)

- Stores **user-defined rules** (e.g. “always replace Save Image with Preview Image”) and preferences (default node types, etc.) in a form the code can apply reliably.
- **SQLite** is a good fit: one file in the workspace, portable, easy to query and export.
- This is the source of truth for “what to do” when creating or modifying workflows.

### 1.2 Narrative and personality (file-based, OpenClaw-style)

- **SOUL.md**, **goals.md**, and a **skills/** folder with one .md per skill in natural language. The LLM reads these to define “who” the agent is and how it should behave.
- Lives in the assistant’s workspace (e.g. under .agents/ or a dedicated folder). Easy for the user or the agent to edit (e.g. “create a new skill” = new file).
- Complements the structured store: rules are applied in code; narrative and skills in prose guide the model’s decisions and tone.

### 1.3 Semantic retrieval (optional — embeddings)

- **Optional** layer: store summaries or chunks of past context with **embeddings** and retrieve the most relevant ones for the current turn (to reduce tokens and improve coherence).
- **Not all LLMs provide an embedding API** (e.g. many chat-only providers do not). The design **must not depend** on embeddings: user context must work with only the structured store and the file-based narrative.
- **When embeddings are available** (same provider or external embedding API): add this layer on top (e.g. a table or index of embeddings in the workspace). When they are not: use a **fixed window** of recent messages or a **short summary** updated each session, stored in the DB or in a .md file, so the agent still has recent context without semantic search.

### 1.4 First-time onboarding (OpenClaw-style)

- **On first contact**, before the agent behaves as the main assistant, the user **defines the personality** the agent should adopt (e.g. more technical, more didactic, more concise). The agent then **asks the user a short set of questions** to bootstrap context: goals with ComfyUI (e.g. “create images for social media”, “learn how workflows work”), experience level (novice, intermediate, advanced), and any other relevant preferences. The answers are persisted (e.g. into SOUL.md / goals.md and the structured store) so that from the second session onward the agent already has this profile and does not need to ask again unless the user wants to update it.
- This onboarding can be a short conversational flow (agent asks, user answers; agent confirms and writes to the workspace). Optionally, the user can skip or defer and the agent falls back to a neutral default personality and no prior goals until the user provides them later.

---

## 2. Awareness of the user’s ComfyUI environment

The **back agent** is responsible for reading the ComfyUI installation: when the UI agent needs to know installed nodes or models, it delegates to the back agent. The back agent scans **custom_nodes/** and **models/** (and, where present, each custom node’s **.agents/** and **.agents/skills/**), builds an environment context, and writes it into the shared **.agents/** so the UI agent can use it in the same or next turn. This does not depend on the ComfyUI API exposing node or model lists and supports the goal of node authors adding their own .agents/skills per node.

**Security model:**

- **Read-only outside workspace** — The back agent may **read** the user’s installation (custom_nodes, models, other nodes’ .agents/) but must **not modify** it. The only place the assistant may **write** is its own **workspace** under the custom node (user context, user rules, shared .agents/ context, caches).
- **Untrusted content** — Content read from third-party custom nodes’ `.agents/skills` must be treated as untrusted (prompt injection / malicious content risk). It must be sanitized or constrained before being injected into either agent’s context.
- **Minimal read** — Read only what is strictly needed to build the environment context.

---

## 3. Knowledge of the ComfyUI ecosystem (OOB and custom nodes)

This is achieved by combining **user context** and **environment awareness**: the back agent (or a dedicated process) gathers documentation and skills from built-in (OOB) nodes and from custom nodes’ `.agents/` and `.agents/skills/`, and writes that knowledge into the shared context (e.g. under .agents/) so the UI agent has a clear picture of the ComfyUI ecosystem and can suggest nodes, workflows, or removals (e.g. “use built-in instead of this custom node”).

---

## 4. Applying workflow changes

Two ways to apply changes to the workflow:

- **Incremental (UI agent)** — The UI agent uses frontend tools (add node, remove node, connect nodes, read workflow) to change the graph step by step. Suitable for small or interactive edits.
- **By delegation (back agent)** — For complex workflows, the UI agent **delegates** the task to the back agent: “build and apply this workflow.” The back agent constructs the graph (e.g. as JSON), applies it via the ComfyUI API, and writes status or result into .agents/ so the UI agent can report back to the user. This avoids a long sequence of add/connect calls from the frontend and keeps complex logic and API usage on the backend.

---

## 5. Inputs: chat and graph (image/video)

Besides chat messages and **attachments**, the agent can receive image/video from **custom nodes** in the graph that send their outputs to the agent (chat extended into the graph). The design should account for this channel (e.g. how those nodes send data to the backend or UI agent, and how it is passed into the multimodal LLM context). See [features](comfyui_assistant_features.md) for the product intent.
