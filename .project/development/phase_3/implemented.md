# Phase 3 — Environment awareness, search, and create_skill

**Status**: Done

## Deliverables

### Sub-phase 3a: Environment scanner + create_skill

- **`environment_scanner.py`** — Scans ComfyUI installation: installed node types (from `nodes.NODE_CLASS_MAPPINGS`), custom node packages (from `custom_nodes/` directory), and models (via `folder_paths`). Caches results to `user_context/environment/*.json`. Provides search and summary functions.
- **`skill_manager.py`** — Creates, lists, and deletes persistent user skills in `user_context/skills/<slug>/SKILL.md` with YAML frontmatter.
- **`api_handlers.py`** — Extracted API endpoint handlers for environment, documentation, and skill management.
- **Frontend tools**: `createSkill`, `deleteSkill`, `updateSkill`, `refreshEnvironment` — Zod schemas + fetch-based implementations calling backend API.
- **System prompt injection**: Environment summary (~200 chars) injected via `agent_prompts.get_system_message(environment_summary=...)`.
- **`tools_definitions.py`** made single source of truth — `__init__.py` imports `TOOLS` from it.

### Sub-phase 3b: Search and documentation tools

- **`documentation_resolver.py`** — Resolves documentation from `NODE_CLASS_MAPPINGS` (inputs/outputs), custom node `.agents/` and `README.md`, and system context skills. Truncates third-party content to 2000 chars for security.
- **Frontend tools**: `searchInstalledNodes`, `readDocumentation` — search cached node data and fetch documentation.

### Sub-phase 3c: Auto-scan, polish, documentation

- **Auto-scan on startup** — Non-blocking initial environment scan scheduled after route registration with 5-second delay.
- **API handler extraction** — Phase 3 handlers moved to `api_handlers.py`; `__init__.py` imports and registers routes.
- **Documentation** — Updated project context, tools docs, and roadmap.

## New files (15)

| File | Purpose |
|------|---------|
| `environment_scanner.py` | Scan ComfyUI installation |
| `skill_manager.py` | Create/manage user skills |
| `api_handlers.py` | Extracted endpoint handlers |
| `documentation_resolver.py` | Resolve documentation for topics |
| `ui/src/tools/definitions/create-skill.ts` | createSkill schema |
| `ui/src/tools/definitions/delete-skill.ts` | deleteSkill schema |
| `ui/src/tools/definitions/update-skill.ts` | updateSkill schema |
| `ui/src/tools/definitions/refresh-environment.ts` | refreshEnvironment schema |
| `ui/src/tools/definitions/search-installed-nodes.ts` | searchInstalledNodes schema |
| `ui/src/tools/definitions/read-documentation.ts` | readDocumentation schema |
| `ui/src/tools/implementations/create-skill.ts` | createSkill implementation |
| `ui/src/tools/implementations/delete-skill.ts` | deleteSkill implementation |
| `ui/src/tools/implementations/update-skill.ts` | updateSkill implementation |
| `ui/src/tools/implementations/refresh-environment.ts` | refreshEnvironment implementation |
| `ui/src/tools/implementations/search-installed-nodes.ts` | searchInstalledNodes implementation |
| `ui/src/tools/implementations/read-documentation.ts` | readDocumentation implementation |
| `system_context/skills/04_environment_tools/SKILL.md` | LLM guidance for new tools |
| `.project/development/phase_3/implemented.md` | This file |

## Modified files (12)

| File | Changes |
|------|---------|
| `__init__.py` | Import from tools_definitions.py, use api_handlers.py, auto-scan, env summary injection |
| `tools_definitions.py` | Add tool definitions (createSkill, deleteSkill, updateSkill, refreshEnvironment, searchInstalledNodes, readDocumentation) |
| `agent_prompts.py` | Add `environment_summary` param to `get_system_message()` |
| `user_context_loader.py` | Add `load_environment_summary()` |
| `user_context_store.py` | Add `ensure_environment_dirs()` |
| `ui/src/tools/definitions/index.ts` | Re-export 4 new definitions |
| `ui/src/tools/implementations/index.ts` | Re-export 4 new implementations |
| `ui/src/hooks/useComfyTools.ts` | Register 4 new tools |
| `system_context/01_role.md` | Mention environment and skill capabilities |
| `.agents/project-context.md` | Updated architecture, tools, endpoints |
| `doc/roadmap.md` | Mark Phase 3 as Done |
| `doc/base-tools.md` | Add new tools documentation |

## API endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/environment/scan` | POST | Trigger full environment scan |
| `/api/environment/summary` | GET | Brief summary for prompt injection |
| `/api/environment/nodes` | GET | Search installed node types (`?q=...&category=...&limit=20`) |
| `/api/environment/models` | GET | List models by category |
| `/api/environment/packages` | GET | List custom node packages |
| `/api/environment/docs` | GET | Fetch documentation (`?topic=...&source=any`) |
| `/api/user-context/skills` | POST | Create skill (`{name, description, instructions}`) |
| `/api/user-context/skills` | GET | List all user skills |
| `/api/user-context/skills/{slug}` | DELETE | Delete skill by slug |
| `/api/user-context/skills/{slug}` | PATCH | Update skill (`{name?, description?, instructions?}`) |

## Tools added (4)

| Tool | Type | Description |
|------|------|-------------|
| `createSkill` | Backend API | Creates a persistent user skill from a remembered instruction |
| `deleteSkill` | Backend API | Deletes a user skill by slug |
| `updateSkill` | Backend API | Updates a user skill by slug (name, description, instructions) |
| `refreshEnvironment` | Backend API | Rescans the ComfyUI installation |
| `searchInstalledNodes` | Backend API | Searches installed node types by name/category/package/display name/description; cache-first, then ComfyUI `/object_info` API fallback |
| `readDocumentation` | Backend API | Fetches documentation for a node type or topic |
| `getAvailableModels` | Backend API | Lists installed model filenames by category; for model recommendations (e.g. "what do you recommend for hyperrealistic?") |

## Iteration log

- **Tool execution (frontend)** — The LLM was returning `tool_calls` but the frontend never executed them. Patched `@assistant-ui/react-ai-sdk`: `useChatRuntime` now passes an `onToolCall` ref so that when the AI SDK stream delivers `tool-input-available`, the runtime runs the registered tools (e.g. `searchInstalledNodes`, `refreshEnvironment`) and sends results back. Patch file: `ui/patches/@assistant-ui+react-ai-sdk+1.3.6.patch`.
- **searchInstalledNodes behavior** — Search is **cache-first**: reads `user_context/environment/installed_nodes.json` and filters by query/category/limit. If the cache returns 0 results and the user sent a query, a **live fallback** runs: the handler calls `fetch_object_info_from_comfyui()` (GET `/object_info` on the local ComfyUI server) and passes that list to `search_nodes(..., live_nodes_override=...)`; if the API is unavailable, fallback is `scan_installed_node_types()`. So the cache is always queried first for performance; the API is used only when the cache has no matches.
- **Richer node data and search** — Scanner and filter now include **display_name** (from `NODE_DISPLAY_NAME_MAPPINGS` or class attribute) and **description** (first line of docstring). Search matches the query as a substring in name, category, package, display_name, description, and input types (case-insensitive). ComfyUI’s `/object_info` response is converted to the same format via `_object_info_to_node_list()` so live results match what the server exposes.
- **Models via ComfyUI API** — GET `/api/environment/models` uses cache first; when the cache has no models data, the backend calls ComfyUI’s GET `/models` (list categories) and GET `/models/{folder}` (list files per category) and returns the same structure as `models.json`. Shared helper `_get_comfyui_base_url()` and new `fetch_models_from_comfyui()` in `environment_scanner.py`.
