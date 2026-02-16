# Agent instructions

When working on this repository, **read the `.agents/` directory first** for context and conventions.

## Where to look

| Path | Purpose |
|------|---------|
| **`.agents/project-context.md`** | Project overview, architecture, stack, directory structure, env vars |
| **`.agents/conventions.md`** | Code style, Git rules, security, patterns (TypeScript, Python), when to update docs |
| **`.agents/skills/`** | Topic-specific guides: tools, assistant-ui, runtime, streaming, thread-list, setup, installation, primitives |

## Quick rules

- **Context**: Start with `.agents/project-context.md` to understand the app and where things live.
- **Conventions**: Follow `.agents/conventions.md` (English only, security first, no `eval`, Zod validation, etc.).
- **Features**: Use the right skill under `.agents/skills/` (e.g. tools → `skills/tools/`, UI → `skills/assistant-ui/`).
- **Docs**: When you change architecture, patterns, or features, update the relevant files under `.agents/` in the same change.
- **Conversational local flows**: For multi-turn slash-style flows handled in backend (`slash_commands.py`), persist state via hidden assistant HTML comment markers so the next turn can continue without DB state.
- **Backend slash commands**: If a slash command is backend-handled, keep frontend and backend in sync by adding it to `ui/src/slash-commands/commands.ts` and forwarding it in `ui/src/hooks/useSlashCommands.ts`.

All documentation in `.agents/` is in English.
