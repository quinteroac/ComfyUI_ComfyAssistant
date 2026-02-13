# Planning

This directory holds **planning and design documentation** for the project: ideas, implementation notes, roadmaps, and other material that does not map directly to shipped functionality or runnable code.

**Purpose**

- Capture ideas and design decisions before or alongside implementation
- Document implementation plans, alternatives considered, and trade-offs
- Keep a single place for “work in progress” or future work that is not yet in the main docs (e.g. `.agents/` or `README.md`)

**Audience**

- **Humans**: contributors and maintainers who want context on how and why things are planned
- **Agents**: AI assistants that need project context; see [AGENTS.md](../AGENTS.md) and `.agents/` for conventions and where to look first

**Documents in this folder**

- [documentation-update-plan.md](documentation-update-plan.md) — Plan to fix doc-vs-code discrepancies (tools, structure, env vars, API, versions)
- [comfyui_context_management.md](comfyui_context_management.md) — How the system manages context efficiently (system message, continuation, trimming, on-demand skills)
- [comfyui_assistant_features.md](comfyui_assistant_features.md) — Product features and audience
- [comfyui_assistant_design.md](comfyui_assistant_design.md) — Architecture (two agents, .agents/, user context)
- [comfyui_assistant_tools.md](comfyui_assistant_tools.md) — Tools (UI vs back agent)
- [comfyui_assistant_skills.md](comfyui_assistant_skills.md) — Desired skills (base, user, custom node)
- [comfyui_assistant_non_functional_features.md](comfyui_assistant_non_functional_features.md) — NFRs (install, config, security, usability)
- [comfyui_assistant_development_phases.md](comfyui_assistant_development_phases.md) — Phased development plan from MVP to full vision

Use this folder for notes that support the project but are not part of the official user-facing or agent-facing documentation.
