# Context System and Environment

This document explains how the assistant's system prompt is assembled from multiple sources, how the ComfyUI environment is scanned and cached, and how to extend both systems.

> **Agent skills**: For machine-optimized reference, see [`.agents/skills/system-and-user-context/SKILL.md`](../../.agents/skills/system-and-user-context/SKILL.md) and [`.agents/skills/environment-and-models/SKILL.md`](../../.agents/skills/environment-and-models/SKILL.md).

---

## Where does the system prompt come from?

The LLM's system message is assembled from three sources:

1. **System context** (`system_context/`) -- Read-only base instructions checked into the repo. These define the assistant's role, capabilities, and tool usage guidelines.
2. **Environment summary** (`user_context/environment/`) -- A brief description of what's installed (nodes, packages, models), so the LLM knows what's available.
3. **User context** (`user_context/`) -- Per-installation user preferences: personality, goals, rules, and user-created skills.

The assembly happens in `agent_prompts.py` via `get_system_message()`, called on every chat request.

---

## System context layout

The `system_context/` directory contains the base system prompt files. They are concatenated in sorted filename order:

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

**Loading order**: Top-level `.md` files first (sorted), then `skills/*/SKILL.md` (sorted). `README.md` is always skipped.

These files are read-only and checked into version control. To change the base instructions, edit the files here directly.

---

## User context layout

The `user_context/` directory is a writable workspace created on first use. It is gitignored and unique per installation:

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

- **`context.db`** is a SQLite database with three tables: rules, preferences, and meta (tracks onboarding state).
- **`SOUL.md`** and **`goals.md`** are set during onboarding or can be edited manually.
- **`environment/`** holds cached scan results (see "Environment scanning" below).
- **`skills/`** holds user-created skills in the Agent Skills standard format (YAML frontmatter + markdown body).

---

## How the system message is assembled

`get_system_message()` in `agent_prompts.py` combines everything into a single string that becomes the system role message for the LLM:

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

The loading functions all live in `user_context_loader.py`:

| Function | Source | Returns |
|----------|--------|---------|
| `load_system_context(path)` | `system_context/*.md` + `skills/*/SKILL.md` | Concatenated text |
| `load_user_context()` | `context.db` + `SOUL.md` + `goals.md` + `skills/` | Dict with rules, soul_text, goals_text, preferences, skills |
| `load_environment_summary()` | `user_context/environment/summary.json` | Brief text (e.g. "87 packages, 523 node types, 150 models") |
| `load_skills()` | `user_context/skills/*/SKILL.md` | List of (slug, text, is_full) |

---

## Token budgeting

The user context is budget-constrained to avoid bloating the system prompt. Constants in `user_context_loader.py`:

| Constant | Value | Purpose |
|----------|-------|---------|
| `MAX_USER_CONTEXT_CHARS` | 4000 | Total character limit for the user context block |
| `MAX_SKILLS_FULL_CHARS` | 1500 | If all skills fit under this, include full text |
| `MAX_NARRATIVE_CHARS` | 1200 | Max combined length for SOUL + goals text |

When skills exceed `MAX_SKILLS_FULL_CHARS`, they are summarized (truncated with a summary indicator). This ensures the system prompt stays within reasonable token limits regardless of how many skills the user creates.

---

## Environment scanning

The assistant knows what nodes, packages, and models are installed by scanning the ComfyUI environment and caching the results. This is handled by `environment_scanner.py`.

### Key functions

| Function | Purpose |
|----------|---------|
| `scan_environment(output_dir)` | Full scan: nodes, packages, models. Writes JSON caches, returns summary dict |
| `scan_installed_node_types()` | Reads `nodes.NODE_CLASS_MAPPINGS` for all registered node types |
| `scan_custom_node_packages(custom_nodes_dir)` | Walks `custom_nodes/` for package metadata (pyproject.toml) |
| `scan_installed_models()` | Uses `folder_paths` to list models by category |
| `search_nodes(env_dir, query, category, limit)` | Search cached nodes; live API fallback if no results |
| `fetch_object_info_from_comfyui()` | Async GET `/object_info` from ComfyUI's local server |
| `fetch_models_from_comfyui()` | Async GET `/models` and `/models/{folder}` |
| `get_cached_environment(env_dir)` | Read all cached JSONs, return dict |
| `get_environment_summary(env_dir)` | Brief text summary from `summary.json` |

### Cache files

Stored in `user_context/environment/`:

| File | Content |
|------|---------|
| `installed_nodes.json` | All node types with name, category, package, display_name, description, inputs, outputs |
| `custom_nodes.json` | Custom node packages with name, path, has_agents, has_readme, description, version |
| `models.json` | Dict of category -> list of filenames |
| `summary.json` | Brief counts (packages, node types, models) |

Model categories include: `checkpoints`, `loras`, `vae`, `controlnet`, `embeddings`, `upscale_models`, `hypernetworks`, `clip`, `unet`, `diffusion_models`.

### Cache-first strategy

When the LLM (or an API endpoint) queries for nodes or models:

1. **Check cache first** -- `search_nodes()` reads `installed_nodes.json`
2. **Fallback to live API** -- If the cache returns no results, it calls ComfyUI's `/object_info` endpoint directly
3. **Filter** -- Substring match on name, category, package, display_name, description, and input types
4. **Limit** -- Returns up to `limit` results (default 20)

Models follow the same pattern: cache first, live API fallback via `fetch_models_from_comfyui()`.

### Auto-scan on startup

In `__init__.py`, `_auto_scan_environment()` runs as a background task 5 seconds after ComfyUI starts:

- Calls `scan_environment()` to populate all cache files
- Logs the summary to console
- Subsequent requests use cached data for fast responses

To force a rescan, you can: (1) have the LLM call the `refreshEnvironment` tool, (2) POST `/api/environment/scan`, or (3) restart ComfyUI (auto-scan runs after 5s).

---

## How to extend

### Adding a new type of user context

1. Store the data in `user_context/` (as a file or in `context.db`).
2. Add a loading function in `user_context_loader.py` to read it.
3. Include the loaded data in `format_user_context()` in `agent_prompts.py`.

### Adding a new scan target

1. Add a new scan function in `environment_scanner.py` (e.g., `scan_installed_workflows()`).
2. Write the results to a new JSON cache file in `user_context/environment/`.
3. Register the function in `scan_environment()` so it runs during full scans.
4. If the LLM should be able to query it, add a backend API endpoint (see [backend.md](backend.md)) and a tool (see [tools.md](tools.md)).

### Adding a new model category

Add the folder name to the categories list in `scan_installed_models()` in `environment_scanner.py`. The category maps to ComfyUI's `folder_paths` system.

### Changing token budgets

Edit the constants in `user_context_loader.py`: `MAX_USER_CONTEXT_CHARS`, `MAX_SKILLS_FULL_CHARS`, `MAX_NARRATIVE_CHARS`.

### Changing the injection order

Edit `get_system_message()` in `agent_prompts.py` -- it controls the concatenation order of all context sections.

---

## How do I...

**...see what the final system prompt looks like?**
Set `COMFY_ASSISTANT_LOG_LEVEL=DEBUG` in `.env`. The assembled system message is logged on each chat request.

**...add base instructions that all users see?**
Add or edit files in `system_context/`. They are loaded in sorted filename order.

**...add user-specific instructions?**
Users can create rules (stored in `context.db`) or skills (stored in `user_context/skills/`). Both are injected into the user context section of the system prompt.

**...understand why a skill was summarized instead of included in full?**
Check the total character count of all skills against `MAX_SKILLS_FULL_CHARS` (1500 chars). If the total exceeds the budget, skills are summarized.

---

## Related docs

- [Architecture](architecture.md) -- Where context assembly fits in the request flow
- [Backend](backend.md) -- The chat handler that calls the context pipeline
- [Tools](tools.md) -- Environment tools that query cached data
- [Frontend](frontend.md) -- Onboarding flow that populates user context
