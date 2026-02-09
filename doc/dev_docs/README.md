# Developer documentation

This folder contains documentation for **developers and contributors** to ComfyUI Assistant. The same standards and conventions described here are used by **AI agents** working on the project (see [AGENTS.md](../../AGENTS.md) and the [.agents/](../../.agents/) directory).

## Contents

| Document | Description |
|----------|-------------|
| [Standards and conventions](standards-and-conventions.md) | Summary of development conventions (code, Git, security, docs). Full source of truth: [.agents/conventions.md](../../.agents/conventions.md). |
| [Vibecoders guide](vibecoders-guide.md) | What to ask AI agents to review before commit, before PR, and when changing code or docs. Prompt templates and checklists. |
| [Health check](health-check.md) | Pre-commit check report: typecheck, lint, format, tests, build, and npm audit. Run these before committing. |

## For AI agents

Agents should read **.agents/** first:

- [.agents/project-context.md](../../.agents/project-context.md) — Project overview, architecture, directory structure.
- [.agents/conventions.md](../../.agents/conventions.md) — Full conventions (security, language, TypeScript/Python, Git, testing, documentation maintenance).
- [.agents/skills/](../../.agents/skills/) — Topic-specific guides (tools, assistant-ui, runtime, etc.).

The files in `doc/dev_docs/` are a **human-oriented** view of the same standards and a guide for using agents effectively.
