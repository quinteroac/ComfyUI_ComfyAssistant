# Vibecoders guide — What to ask agents to review

This document is for **vibecoders**: people who build features with AI assistants (e.g. Cursor, Claude, Copilot) and want to keep the project consistent and safe. It lists **what you should ask the agent to review** and gives **ready-to-use prompts** you can paste into the chat.

The project uses the same standards for humans and agents; see [Standards and conventions](standards-and-conventions.md) and the full [.agents/conventions.md](../../.agents/conventions.md).

---

## Project-specific agent skills

The project has agent skills under `.agents/skills/` that give agents deep context about each area of the system. When you ask an agent to work on a specific area, point it to the relevant skill so it understands the architecture, patterns, and file locations.

| Skill | Topic area | When to point the agent here |
|-------|-----------|------------------------------|
| `architecture-overview` | System overview, request flow, agentic loop | First time working on the project; understanding the system |
| `backend-architecture` | Python modules, API endpoints, SSE streaming | Changing backend code, adding endpoints |
| `backend-tools-declaration` | Tool definitions, frontend/backend sync | Adding or modifying tools |
| `system-and-user-context` | System prompt assembly, context loading | Changing prompts, user context, skill injection |
| `environment-and-models` | Environment scanning, model discovery, caching | Changing scans, model lists, cache strategy |
| `ui-integration` | ComfyUI extension registration, bottom panel, `window.app` | Changing extension setup, tab config, slash commands |
| `assistant-ui` | Chat UI components, terminal theme, message rendering | Changing chat appearance, composer, onboarding |
| `patterns-and-conventions` | Quick-reference of coding conventions | Before any code change (quick style check) |
| `documentation` | When and how to update docs | After making changes (doc update rules) |

Each skill has a corresponding human-readable developer doc in `doc/dev_docs/` -- see [architecture.md](architecture.md), [backend.md](backend.md), [context-and-environment.md](context-and-environment.md), [frontend.md](frontend.md), and [tools.md](tools.md).

### The documentation skill

The `documentation` skill ([.agents/skills/documentation/SKILL.md](../../.agents/skills/documentation/SKILL.md)) defines when and how to update documentation:

- **When** to update docs (architecture, patterns, new features, phase work, user-facing changes)
- **What** to update: sources of truth (project-context, conventions, skills, .project/development/, doc/, README, tools_definitions)
- A **checklist** before marking a change complete
- Rules for **phase implementation** (`.project/development/<phase>/implemented.md`) and **documentation debt**

When you want the agent to handle doc updates in line with the project rules, ask it to **read and apply the documentation skill** (see prompt below). The skill mirrors the Documentation Maintenance Protocol in `.agents/conventions.md` and keeps doc updates consistent.

---

## When to ask for a review

Ask the agent to review in these situations:

| When | What to ask |
|------|-------------|
| **Before committing** | Conventions check, typecheck, lint, and that docs were updated if needed. |
| **Before opening a PR** | Full checklist: security, tests, docs, commit message style. |
| **After adding a feature** | That `.agents/project-context.md` and any relevant skill docs are updated; that new tools are in both frontend and backend. |
| **After changing architecture or patterns** | That `.agents/conventions.md` and related docs reflect the new approach. |
| **After touching user-facing behavior** | That `doc/` or README is updated. |
| **When adding a new tool** | Definition + implementation + backend declaration + system prompt / skills; no secrets; Zod validation. |

---

## Prompts you can use

Copy and paste these (and adjust paths or scope as needed). Prefer being specific (e.g. “review `ui/src/tools/implementations/set-node-widget-value.ts`”) so the agent focuses on the right files.

### 1. General conventions review

```
Review my changes against the project conventions in .agents/conventions.md. Check: code style (ESLint/Prettier, TypeScript strict, no any), security (no secrets, Zod validation, no eval), naming and file structure, and that any new or changed behavior is documented in .agents/ or doc/ as needed.
```

### 2. Before commit — full pass

```
Before I commit, please:
1. Run typecheck and lint in ui/ and fix any issues.
2. Check that my changes follow .agents/conventions.md (security, validation, naming, English only).
3. If I changed architecture, a feature, or user-facing behavior, list which docs in .agents/ or doc/ need to be updated and propose the edits.
4. Suggest a conventional commit message (type(scope): description) for my staged changes.
Do not run git commit unless I explicitly ask you to.
```

### 3. Security and validation focus

```
Review the files I changed for security and validation: no API keys or secrets in code, no eval(), no dangerouslySetInnerHTML with user input, and that all external/LLM inputs are validated with Zod (or equivalent). Flag anything that could expose data or run untrusted code.
```

### 4. Documentation sync

```
I changed [describe what: e.g. added a new tool, changed the context flow]. According to .agents/conventions.md (Documentation Maintenance Protocol), which files must be updated? List them and update them: .agents/project-context.md, .agents/conventions.md, .agents/skills/*, doc/dev_docs/*, README, .project/development/* as applicable. Check the project-specific skills (architecture-overview, backend-architecture, backend-tools-declaration, system-and-user-context, environment-and-models, ui-integration, assistant-ui) and update any that are affected by this change.
```

### 5. New tool checklist

```
I added a new tool [name]. Please verify:
1. Frontend: definition (Zod schema) in ui/src/tools/definitions/, implementation in ui/src/tools/implementations/, registered in ui/src/tools/index.ts.
2. Backend: declared in tools_definitions.py and __init__.py (if needed).
3. System prompt / system_context or skills: agent knows when and how to use the tool.
4. No secrets in frontend; validation for all inputs.
5. .agents/project-context.md and .agents/skills/tools/ (or relevant skill) updated. If user-facing, doc/base-tools.md or doc/ updated.
```

### 6. Phase implementation doc

```
I implemented [phase name]. Create or update .project/development/<phase_name>/implemented.md with: deliverables, files and routes changed, and a short iteration log entry, following the format of .project/development/phase_1/implemented.md and .project/development/phase_2/implemented.md.
```

### 7. Quick “did I miss any docs?”

```
I changed [brief description]. Per the Documentation Maintenance Protocol in .agents/conventions.md, did I miss updating any of: .agents/project-context.md, .agents/conventions.md, .agents/skills/, doc/, README, or .project/development/? If yes, update them.
```

### 8. Apply the documentation skill

Use this when you want the agent to follow the project's documentation-update rules (sources of truth, checklist, same-commit rule):

```
Read and apply the documentation skill: .agents/skills/documentation/SKILL.md. My change: [describe what you changed]. List which docs are affected according to that skill, then update them in line with the checklist and sources of truth. Do not leave documentation out of date.
```

For phase work only:

```
I implemented [phase name]. Apply the documentation skill (.agents/skills/documentation/SKILL.md) for phase implementation: create or update .project/development/<phase_name>/implemented.md with deliverables, files changed, and iteration log, following the format of existing .project/development/phase_0/phase_1/phase_2.
```

### 9. Understand the architecture

Use this when you want the agent to understand how the project works before making changes:

```
Read the architecture-overview skill (.agents/skills/architecture-overview/SKILL.md) and the relevant skills for the area I need to change: [list area, e.g. backend, tools, UI, context]. Then read the corresponding developer docs in doc/dev_docs/ (architecture.md, backend.md, tools.md, frontend.md, context-and-environment.md). Summarize how the area works and which files I need to touch for my change: [describe change].
```

---

## Checklist you can paste to the agent

Use this as a reminder for the agent (and for yourself) before commit or PR:

```
Apply the following checklist to my changes (fix or report):

Code & style
- [ ] TypeScript: strict types, no any; Zod for external input
- [ ] Python: type hints, docstrings for public functions
- [ ] ESLint/Prettier (ui/): typecheck, lint, format
- [ ] Naming: kebab-case/PascalCase (TS), snake_case (Python), file names per conventions

Security
- [ ] No API keys or secrets in code; use .env
- [ ] No eval(); no dangerouslySetInnerHTML with raw user content
- [ ] Inputs validated (Zod or equivalent)

Git
- [ ] Conventional commit message: type(scope): description
- [ ] Small, focused commits; current state committed before big refactors

Documentation
- [ ] If architecture/pattern/feature changed: .agents/project-context.md, .agents/conventions.md, relevant .agents/skills/ updated
- [ ] If user-facing: doc/ or README updated
- [ ] If implementing a phase: .project/development/<phase>/implemented.md added or updated

Tests & build
- [ ] npm test passes; npm run build passes in ui/
- [ ] New or changed behavior has or updates tests as appropriate
```

---

## Tips for working with agents

1. **Point to .agents/** — Say "read .agents/project-context.md and .agents/conventions.md first" so the agent uses the same rules as the project.
2. **Use project-specific skills** — Before working on a specific area, point the agent to the right skill (see the table in "Project-specific agent skills" above). For example: "read the backend-architecture skill before changing the API endpoints."
3. **Scope the review** — "Review only the files in ui/src/tools/implementations/" avoids noise and focuses the agent.
4. **Ask for docs explicitly** — Agents sometimes skip doc updates; use the "Documentation sync" or "did I miss any docs?" prompts, or ask the agent to **apply the documentation skill** (.agents/skills/documentation/SKILL.md) so it follows the project's doc-update rules (prompt 8 above).
5. **No auto-commit** — Conventions say the agent must not run `git commit` without your explicit approval; remind the agent if needed.
6. **Use the checklist** — Pasting the checklist (or the "Before commit" prompt) before each commit helps catch missing docs, security issues, and style problems.

---

## Related

- [Architecture](architecture.md) — System overview, request flow, agentic loop.
- [Backend](backend.md) — Python modules, API endpoints, SSE streaming.
- [Context and environment](context-and-environment.md) — System prompt assembly, environment scanning.
- [Frontend](frontend.md) — React components, ComfyUI integration, theme.
- [Tools](tools.md) — Step-by-step guide for adding and modifying tools.
- [Standards and conventions](standards-and-conventions.md) — Summary of what agents and humans follow.
- [.agents/conventions.md](../../.agents/conventions.md) — Full conventions (agents' source of truth).
- [.agents/project-context.md](../../.agents/project-context.md) — Architecture and layout (agents read this first).
- [.agents/skills/documentation/SKILL.md](../../.agents/skills/documentation/SKILL.md) — Documentation skill: when and how to update docs (ask the agent to apply this for doc updates).
