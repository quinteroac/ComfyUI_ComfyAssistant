# Documentation update protocol (reference)

This file is a quick reference for the documentation skill. The canonical text is in [.agents/conventions.md](../../../conventions.md) (Documentation Maintenance Protocol).

## Triggers → Files to update

| Trigger | Files to update |
|--------|------------------|
| **Architecture** (design, data flows, integrations) | `.agents/project-context.md`, `.agents/skills/tools/references/architecture.md` if tools affected, READMEs, API docs |
| **Patterns** (error handling, state, validation, testing) | `.agents/conventions.md`, `.agents/skills/*/references/*.md`, README examples |
| **New feature** (tool, component, API) | `.agents/project-context.md`, relevant `.agents/skills/`, `README.md`, `doc/` if user-facing, `tools_definitions.py` + frontend if tool |
| **Phase work** | `.project/development/<phase_name>/implemented.md` |
| **User-facing** | `doc/`, `README.md` |

## Sources of truth table

| Source | Purpose |
|--------|---------|
| `.agents/project-context.md` | Architecture, stack, structure, features |
| `.agents/conventions.md` | Standards and patterns |
| `.agents/skills/*` | Topic guides (tools, assistant-ui, runtime, etc.) |
| `.project/development/` | Phase implementation docs |
| `.project/planning/` | Planning and design (new planning docs go here) |
| `README.md` | User-facing overview and usage |
| `doc/` | User docs + dev_docs |
| `tools_definitions.py` | Backend tool declarations |

## Rules

1. Update docs in the **same** commit/PR as the code.
2. Do not defer documentation; no "documentation PR later."
3. If you discover outdated docs, fix or file an issue; do not ignore.
