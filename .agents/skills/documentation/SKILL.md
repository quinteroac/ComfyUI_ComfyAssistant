---
name: documentation
description: When and how to update project documentation. Use whenever you change architecture, patterns, features, or user-facing behavior; or when implementing a development phase.
---

# Documentation updates

**Golden rule:** If code changes, documentation changes. Update docs in the **same** commit or PR as the code. Do not defer documentation to "later" or a separate PR.

## When to update documentation

| Trigger | What to update (see below) |
|--------|----------------------------|
| **Architecture changes** | project-context, skills (e.g. tools), READMEs, API docs |
| **Pattern or practice changes** | conventions.md, relevant skill references, README examples |
| **New feature (tool, component, API)** | project-context, relevant skill, README, tool defs if tools |
| **Phase implementation or iteration** | `.project/development/<phase_name>/implemented.md` |
| **User-facing behavior or usage** | `doc/`, README |
| **New or changed endpoints, routes** | project-context, API docs, README if user-facing |

Before committing any such change, ask: **"What documentation does this change affect?"** Then update all affected files.

## Sources of truth (what to update)

| File / directory | Purpose | Update when |
|------------------|---------|-------------|
| `.agents/project-context.md` | Project overview, architecture, structure, features | Architecture, stack, structure, or new features |
| `.agents/conventions.md` | Development standards | New or changed patterns, practices |
| `.agents/skills/<topic>/` | Topic-specific guides (e.g. tools, runtime) | That area changes (e.g. new tool → tools skill) |
| `.project/development/<phase>/implemented.md` | Phase deliverables and iteration log | Implementing or iterating that phase |
| `.project/planning/` | Planning, design, WIP | New planning docs go here (not at root) |
| `README.md` | User-facing overview and usage | Feature or usage changes |
| `doc/` | User and developer docs (installation, config, skills, tools, roadmap, dev_docs) | User-facing behavior, setup, or dev process |
| `tools_definitions.py` | Backend tool declarations | Any tool addition or change |

Details and examples: [.agents/conventions.md](../../conventions.md) — "Documentation Maintenance Protocol" and "Documentation Sources of Truth".

## Checklist before marking a change complete

- [ ] Updated `.agents/project-context.md` if architecture, structure, or features changed
- [ ] Updated `.agents/conventions.md` if patterns or practices changed
- [ ] Updated relevant `.agents/skills/` (e.g. tools, setup) if that area changed
- [ ] Updated `README.md` if usage or features changed
- [ ] Updated `doc/` if user-facing behavior, setup, or dev process changed
- [ ] Added or updated `.project/development/<phase>/implemented.md` if implementing or iterating a phase
- [ ] Updated tool definitions (frontend + `tools_definitions.py`) if tools changed
- [ ] Added or updated JSDoc / docstrings for new or changed code
- [ ] Verified links and references in updated docs still work

## Phase implementation

When implementing or iterating a **development phase**:

1. Create or use the folder `.project/development/<phase_name>/` (e.g. `.project/development/phase_3/`).
2. Add or update `implemented.md` in that folder with:
   - Summary and status
   - Deliverables (what was built)
   - Files and routes changed
   - Short iteration log
3. Follow the format of existing `.project/development/phase_0/implemented.md`, `phase_1/implemented.md`, `phase_2/implemented.md`.

## Outdated documentation

- If you find outdated docs: fix them in the same change set if small; otherwise fix in a focused follow-up. Do not leave them outdated.
- Do not create documentation debt: document as you code, not after.

## References

- [./references/update-protocol.md](./references/update-protocol.md) — Triggers and sources-of-truth quick reference
- [.agents/conventions.md](../../conventions.md) — Full Documentation Maintenance Protocol (sections 1–8)
- [doc/dev_docs/standards-and-conventions.md](../../../doc/dev_docs/standards-and-conventions.md) — Developer-facing summary
