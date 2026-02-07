# ComfyUI Assistant — description and features

This document outlines what the assistant should do and what its characteristics are. It is for ideas and clarity only; implementation will be planned later. It is not an execution or formal specification.

---

## Audience

- **Novice and experienced ComfyUI users.** Users may be technical or non-technical, so the assistant must be **user-friendly**.

---

## Purpose

- **Support workflows and the ComfyUI interface** — Help with workflow design and general use of the UI.
- **Build basic and advanced workflows** — Enable users to solve complex tasks (image, video, music, and other ComfyUI capabilities).
- **Automation** — Support automation for image, video, music, and other content creation that ComfyUI allows.
- **Prompt design and media analysis** — Assist with prompt design and analysis of images and videos (see *Considerations* below for how the agent receives image/video input).

---

## How the agent should achieve this

- **User context**
  - Know the user’s context: background (capabilities, skills, expertise) and goals.
  - **Persist context across sessions** so the agent can improve over time and to reduce token usage (avoid re-establishing full context in every session).

- **ComfyUI environment**
  - Be aware of the user’s ComfyUI environment: the current project and what is installed.
  - Know the user’s **custom nodes** (when available) and **personalizations** (user-defined rules; see *Considerations*).

- **Node ecosystem**
  - Know built-in (OOB) nodes and **custom nodes available for ComfyUI** in general.
  - Suggest installing new nodes or removing redundancy (e.g. if the user has a custom node that duplicates a built-in node, suggest using the built-in one and uninstalling the custom node).

---

## Considerations and clarifications

### Image and video analysis

- Besides **chat attachments**, the agent can receive image/video through **custom nodes** that take image or video outputs and send them to the agent — i.e. the chat is extended into the graph via nodes that act as context sources.
- The LLM is assumed **multimodal** (e.g. Grok, Claude, Gemini, ChatGPT with vision) so the agent can describe, tag, or suggest changes based on the media it receives.

### Knowing installed nodes and models

- A **backend component** of the assistant can scan the ComfyUI installation (e.g. **custom_nodes/** and **models/**) and build an environment context, then pass it to the UI agent. This does not depend on the ComfyUI API exposing node/model lists.
- This approach is **more powerful** for the goal of having custom node developers add their own **.agents/skills** per node: the backend reads those directories and merges that knowledge into the agent’s context.
- For **very complex workflows**, building the graph as **JSON** and uploading it via an API (e.g. to the backend, which then applies it via ComfyUI API) may be better than many small “add node / connect” calls from the frontend. A backend agent enables this and opens more possibilities.

### Personalization (user-defined rules)

- **Personalization** means **user-defined tasks/rules** that the agent applies when creating or modifying workflows.
- Example: many users prefer **Preview Image** over **Save Image** and download manually; shared workflows often use Save Image. A **user skill** could be: “Always replace ‘Save Image’ nodes with ‘Preview Image’.” Once defined, whenever the user asks for something that would add Save Image, the agent applies the substitution.
- Such rules are stored as part of **user context** (persisted across sessions) and give concrete content to “user skills” in the skills model.

---

## Additional features (candidates)

- **Templates and “start from…”** — Suggest or apply starter workflows (e.g. basic txt2img, img2img, upscale) so novices can begin from a known-good graph.
- **Debugging and execution errors** — When a run fails (red node, type mismatch, missing input), interpret the error (if exposed by API or logs) and suggest concrete fixes to the workflow.
- **Explain node or connection** — Given a node or a wire, return a short natural-language description of what it does (using workflow read + documentation in .agents/skills).
- **Recent workflow change history** — Optionally track last N changes (add/remove/connect) so the agent can suggest “undo X” or “revert to before…” (advanced).
- **Suggest optimizations** — e.g. “You have two CheckpointLoaders; you could reuse one,” or “This KSampler could go after the upscale.” Requires rules or knowledge in skills; valuable for power users.
- **Slot type compatibility** — When connecting, check or warn if output and input types are compatible (if ComfyUI API exposes slot types), to reduce connection errors.
- **Multi-language consistency** — Ensure agent responses and any generated UI text respect the user’s language (reinforces user-friendly for non-technical users).
- **Export / import “conversation + workflow”** — Save a snapshot (workflow + conversation summary) to resume or share later; complements persistent context and helps support and learning.
