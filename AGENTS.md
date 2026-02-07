# Agent instructions

When working on this repository, **read the `.agents/` directory first** for context and conventions.

## Where to look

| Path | Purpose |
|------|---------|
| **`.agents/project-context.md`** | Project overview, architecture, stack, directory structure, env vars |
| **`.agents/conventions.md`** | Code style, Git rules, security, patterns (TypeScript, Python), when to update docs |
| **`.agents/skills/`** | Topic-specific guides: tools, assistant-ui, runtime, streaming, thread-list, setup, primitives |

## Quick rules

- **Context**: Start with `.agents/project-context.md` to understand the app and where things live.
- **Conventions**: Follow `.agents/conventions.md` (English only, security first, no `eval`, Zod validation, etc.).
- **Features**: Use the right skill under `.agents/skills/` (e.g. tools → `skills/tools/`, UI → `skills/assistant-ui/`).
- **Docs**: When you change architecture, patterns, or features, update the relevant files under `.agents/` in the same change.

All documentation in `.agents/` is in English.
