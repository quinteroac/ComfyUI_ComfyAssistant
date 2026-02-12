---
name: system-and-user-context
description: System prompt assembly from system_context, user_context, and environment sources
version: 0.0.1
license: MIT
---

# System and User Context

The LLM's system message is assembled from three sources: `system_context/`, environment data, and `user_context/`. This skill explains the layout, loading pipeline, and token budgeting.

## `system_context/` Layout

Read-only base system prompt. Files are concatenated in sorted filename order:

```
system_context/
├── 01_role.md                         # Base role and capabilities
├── skills/                            # Base capability skills
│   ├── 01_base_tools/SKILL.md         # Tool usage instructions
│   ├── 02_tool_guidelines/SKILL.md    # When and how to use tools
│   ├── 03_node_reference/SKILL.md     # Common node types reference
│   ├── 04_environment_tools/SKILL.md  # Environment tool instructions
│   └── 05_workflow_execution/SKILL.md # Workflow execution guidance
└── README.md                          # (skipped during loading)
```

Loading order: top-level `.md` files first (sorted), then `skills/*/SKILL.md` (sorted). `README.md` is skipped.

## `user_context/` Layout

Writable user workspace, created on first use:

```
user_context/
├── context.db          # SQLite: rules (name, rule_text), preferences (key/value), meta (onboarding_done)
├── SOUL.md             # Personality / tone (from onboarding or manual edit)
├── goals.md            # User goals and experience level
├── environment/        # Cached environment scan data
│   ├── installed_nodes.json
│   ├── custom_nodes.json
│   ├── models.json
│   └── summary.json
└── skills/             # User skills (Agent Skills standard)
    └── <slug>/SKILL.md # e.g. use-preview-image/SKILL.md
```

## Loading Pipeline

All loading functions live in `user_context_loader.py`:

| Function | Source | Returns |
|----------|--------|---------|
| `load_system_context(path)` | `system_context/*.md` + `skills/*/SKILL.md` | Concatenated text |
| `load_user_context()` | `context.db` + `SOUL.md` + `goals.md` + `skills/` | Dict with rules, soul_text, goals_text, preferences, skills |
| `load_environment_summary()` | `user_context/environment/summary.json` | Brief text (e.g. "87 packages, 523 node types, 150 models") |
| `load_skills()` | `user_context/skills/*/SKILL.md` | List of (slug, text, is_full) |

### Skill Loading Details

`load_skills()` in `user_context_loader.py`:
- Reads `user_context/skills/*/SKILL.md` (Agent Skills standard with YAML frontmatter)
- Also supports legacy flat `skills/<slug>.md` files
- Parses YAML frontmatter via `_parse_skill_md(content)` to extract name and body
- Applies token budget: if total skill text < 1500 chars, include full text; otherwise summarize

## Token Budgeting Constants

Defined in `user_context_loader.py`:

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_USER_CONTEXT_CHARS` | 4000 | Loader-level budget reference |
| `MAX_SKILLS_FULL_CHARS` | 1500 | If all skills fit under this, use full text |
| `MAX_NARRATIVE_CHARS` | 1200 | Max combined length for SOUL + goals text |

At runtime, `agent_prompts.format_user_context()` also enforces caps for rules, narrative, and skills, then hard-truncates the final block.

`__init__.py` adds env-tunable limits:
- `LLM_SYSTEM_CONTEXT_MAX_CHARS` (default: `12000`)
- `LLM_USER_CONTEXT_MAX_CHARS` (default: `2500`)
- `LLM_HISTORY_MAX_MESSAGES` (default: `24`)
- `LLM_TOOL_RESULT_KEEP_LAST_ROUNDS` (default: `2`) — only the last N "rounds" of tool results are sent in full; older rounds get a short placeholder

## System Message Assembly

`agent_prompts.py` → `get_system_message(system_context_text, user_context, environment_summary)`:

```
{system_context_text}           ← from load_system_context()

## Installed environment
{environment_summary}           ← from load_environment_summary()

---

## User context (rules and skills)

### User rules
- **Rule**: {rule_text}         ← from context.db

### User context
**Personality / tone**: {soul}  ← from SOUL.md
**User goals**: {goals}         ← from goals.md

### User skills
#### User skill: {slug} (summary; apply when relevant)
{skill_text}                    ← from user_context/skills/
```

The assembled message is passed as the system role message to the LLM in `chat_api_handler`.

## FAQ

### Where do base instructions live vs user preferences?
Base instructions: `system_context/` (read-only, checked into repo). User preferences: `user_context/` (writable, per-installation, gitignored).

### How do I add a new kind of user context?
1. Store the data in `user_context/` (file or `context.db`)
2. Add a loading function in `user_context_loader.py`
3. Include the loaded data in `format_user_context()` in `agent_prompts.py`

### How do I tweak the injection order?
Edit `get_system_message()` in `agent_prompts.py` -- it controls the concatenation order.

### How do I change token budgets?
Edit the constants in `user_context_loader.py`: `MAX_USER_CONTEXT_CHARS`, `MAX_SKILLS_FULL_CHARS`, `MAX_NARRATIVE_CHARS`.

## Related Skills

- `environment-and-models` -- how environment data is scanned and cached
- `backend-architecture` -- the chat handler that calls this pipeline
- `architecture-overview` -- where context assembly fits in the request flow
