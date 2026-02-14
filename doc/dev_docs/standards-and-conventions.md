# Standards and conventions

This document summarizes the **development standards and conventions** for ComfyUI Assistant. **Developers and AI agents follow the same rules.** The **single source of truth** is [.agents/conventions.md](../../.agents/conventions.md); this page is a quick reference and overview.

## Why these conventions

- **Consistency** — Same style and patterns across the codebase.
- **Security** — No secrets in code, validation with Zod, no `eval()`, principle of least privilege.
- **Maintainability** — Clear structure, documentation updated with code, conventional commits.
- **Agent alignment** — Agents are instructed to follow `.agents/conventions.md`; humans and agents stay in sync.

---

## Core principles

1. **Security first** — Never expose API keys or user data; validate and sanitize inputs; use Zod; avoid `eval()` and dynamic code execution.
2. **English only** — All code, comments, documentation, and commit messages in English.
3. **ComfyUI compliance** — Follow [ComfyUI Extension Standards](https://docs.comfy.org/custom-nodes/js/javascript_overview) for structure, API usage, and node manipulation.
4. **Constructive challenge** — Agents (and reviewers) should question suboptimal choices, ask for clarity, and suggest better approaches rather than blindly complying.

---

## Code and style

### TypeScript / JavaScript

- **Style:** ESLint + Prettier (single quotes, no semicolons, 2-space indent, ~80 char width).
- **Types:** Strict TypeScript; no `any`; use `unknown` or proper types; interfaces for data structures; `z.infer<>` for Zod schemas.
- **Validation:** Validate external inputs with Zod; use `safeParse` and handle errors.
- **Errors:** Structured results (e.g. `{ success, data?, error? }`); avoid throwing for expected failures.
- **Naming:** `kebab-case.ts` for utilities; `PascalCase.tsx` for React components.

### Python

- **Style:** PEP 8; 4-space indent; snake_case; type hints and docstrings on public functions.
- **Errors:** Handle exceptions; return clear error information to the client.

### File naming

- TypeScript/React: `kebab-case.ts` or `PascalCase.tsx`
- Python: `snake_case.py`
- Docs: `kebab-case.md` or `UPPERCASE.md` (e.g. README.md)

---

## Security

- **Secrets:** Never commit `.env` or API keys; use `.env.example` with placeholders; load via `python-dotenv` or `process.env`.
- **Input:** Always validate (Zod in TS; type checks and sanitization in Python).
- **XSS:** Do not use `dangerouslySetInnerHTML` with user content; use a markdown/sanitization library.
- **Access:** Check `window.app` / graph availability before using ComfyUI APIs.

---

## Git

- **Commits:** Conventional commits: `type(scope): description` (e.g. `feat(tools): add setNodeWidgetValue`). Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `security`.
- **Before big changes:** Commit current state first; prefer small, focused commits. Agents must ask before running `git commit`.
- **Branches:** Descriptive names (e.g. `feature/add-widget-tool`, `fix/stream-handler`).

---

## Testing

- **Unit tests:** Critical paths and tools; mock ComfyUI app where needed.
- **Layout:** `__tests__/` next to implementation (e.g. `ui/src/tools/implementations/__tests__/add-node.test.ts`).
- **Goals:** 80%+ on critical paths; 100% on security-sensitive code; include error and edge cases.

---

## Documentation

- **Comments:** Explain "why", not "what"; document security considerations.
- **Functions:** JSDoc (TypeScript) and docstrings (Python) with params, returns, and examples where helpful.
- **When code or architecture changes:** Update the relevant docs in the **same** change (see [Documentation maintenance](#documentation-maintenance) below).

### Documentation maintenance

If you change **architecture**, **patterns**, or **features**, update:

- `.agents/project-context.md` — When architecture, stack, or structure changes.
- `.agents/conventions.md` — When patterns or practices change.
- Relevant `.agents/skills/` docs — When that area (e.g. tools) changes.
- `README.md` or `doc/` — When user-facing behavior or usage changes.
- `.project/development/<phase>/implemented.md` — When implementing or iterating a phase.

**Golden rule:** If code changes, documentation changes. No exceptions.

---

## Before committing (manual checks)

Pre-commit hooks are currently **disabled**. Run manually from `ui/`:

```bash
npm run typecheck   # TypeScript
npm run lint        # ESLint
npm run format      # Prettier
npm test            # Tests
npm run build       # Build
```

---

## Planning and development phases

- **Planning / design docs** → `.project/planning/` (not at repo root).
- **Phase implementation** → One folder per phase under `.project/development/` (e.g. `.project/development/phase_1/implemented.md`). When implementing or iterating a phase, add or update the `implemented.md` in that folder.

---

## Full reference

For the complete text (code examples, ComfyUI-specific rules, versioning, dependency management, documentation checklist, and enforcement details), see:

**[.agents/conventions.md](../../.agents/conventions.md)**

Agents are instructed to read `.agents/` (including `project-context.md` and `conventions.md`) before making changes.
