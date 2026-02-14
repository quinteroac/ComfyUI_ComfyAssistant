---
name: patterns-and-conventions
description: Quick-reference summary of project conventions for fast agent consumption
version: 0.0.1
license: MIT
---

# Patterns and Conventions

Quick-reference of `.agents/conventions.md`. Read the full file for details; this skill covers the essentials.

## Non-Negotiable Rules

1. **No `eval()` or dynamic code execution** -- ever
2. **No secrets in code or version control** -- use `.env` files
3. **Zod validation on all external inputs** (frontend)
4. **Type hints on all function signatures** (Python)
5. **English only** -- code, comments, docs, commits
6. **Security first** -- when in doubt, choose the safer option

## TypeScript Style

| Rule | Value |
|------|-------|
| Quotes | Single |
| Semicolons | None |
| Indentation | 2 spaces |
| Line width | 80 chars |
| Trailing commas | None |
| Types | Strict mode, no `any`, use `unknown` |
| Schemas | Zod for runtime validation, `z.infer<>` for types |
| Errors | Return `{ success, data?, error? }` -- never throw |
| Imports | core -> third-party -> local |
| Components | Named exports, typed Props interface |

## Python Style

| Rule | Value |
|------|-------|
| Indentation | 4 spaces |
| Naming | `snake_case` functions/vars, `PascalCase` classes |
| Type hints | Required on all signatures |
| Docstrings | Required on all public functions |
| Error handling | Try/except with structured returns |
| Imports | stdlib -> third-party -> local |

## Git Rules

- **Feature branches** for phases and major changes -- merge via PR
- **Conventional commits**: `type(scope): description`
  - Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `security`
- **Branch names**: `feature/add-widget-tool`, `fix/memory-leak-in-stream`
- **Ask before committing** -- never commit without user confirmation
- **Commit before risky changes** -- preserve known-good state

## Documentation Rules

| Directory | Purpose | Examples |
|-----------|---------|---------|
| `.project/planning/` | Ideas, roadmaps, specs, WIP | Feature proposals, phase plans |
| `.project/development/` | Phase implementation records | `phase_1/implemented.md` |
| `.agents/` | Agent skills and project docs | Skills, conventions, project context |
| `doc/` | User and developer documentation | Install guide, tools reference |

**Golden rule**: If code changes, documentation changes -- same PR.

## FAQ

### How do I know which files to update when I change something?
Read the "Documentation Maintenance Protocol" in `.agents/conventions.md` section 7. It has a checklist per change type (architecture, patterns, features).

### Where do planning docs go?
Always under `.project/planning/`. Never at the repo root.

### Where do implementation records go?
Under `.project/development/<phase_name>/implemented.md`.
