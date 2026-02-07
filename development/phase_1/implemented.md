# Phase 1 — Implemented

This document describes what was implemented for **Phase 1 (User context and manual skills)** and will be updated as the phase is iterated or refined.

Reference: [comfyui_assistant_development_phases.md](../../planning/comfyui_assistant_development_phases.md) (Phase 1 section).

---

## Delivered

### 1. Workspace and structured store

- **Path**: `user_context/` under the extension root (see `user_context_path` in `__init__.py`).
- **Creation**: `user_context/` and `user_context/skills/` are created on first use (when loading context or saving onboarding).
- **SQLite** (`user_context/context.db`):
  - **rules**: `id`, `name`, `rule_text`, `created_at`
  - **preferences**: `key`, `value`, `updated_at`
  - **meta**: `key`, `value`, `updated_at` (e.g. `onboarding_done`)
- **Module**: `user_context_store.py` — `get_rules()`, `get_preferences()`, `get_onboarding_done()`, `set_onboarding_done()`, `add_rule()`, `add_or_update_preference()`, `save_onboarding()`, `ensure_user_context_dirs()`.

### 2. File-based narrative and skills

- **SOUL.md**, **goals.md**: plain markdown under `user_context/`; written by onboarding or manually.
- **skills/**: one `.md` file per user skill; filename without extension = slug (e.g. `preview-instead-of-save.md`). Content: optional first heading as title, rest = instructions for the LLM. Skills are **manual** (user or contributor edits files); no `create_skill` tool in Phase 1.
- **Reading**: `user_context_loader.py` — `load_user_context()` returns rules, soul text, goals text, preferences, and skills (full text if total size ≤ 1500 chars, else first-paragraph summaries per file). Constants: `MAX_USER_CONTEXT_CHARS`, `MAX_SKILLS_FULL_CHARS`, `MAX_NARRATIVE_CHARS`.

### 3. Load user context into prompts

- **agent_prompts.py**: `format_user_context(user_context)` builds the "User context" block; `get_system_message(user_context=None)` appends it when `user_context` is provided.
- **chat_api_handler** (in `__init__.py`): before building the system message, calls `user_context_loader.load_user_context()` (with try/except fallback to no context), then `get_system_message(user_context)` so the single system message includes rules, narrative, and skills.

### 4. Optional first-time onboarding

- **Backend**:
  - GET `/api/user-context/status` → `{ "needsOnboarding": true|false }` (based on `get_onboarding_done()`).
  - POST `/api/user-context/onboarding` — body: `{ personality?, goals?, experienceLevel? }` or `{ skip: true }`. Writes SOUL.md, goals.md, preferences, and sets `onboarding_done` via `user_context_store.save_onboarding()`.
- **Frontend**:
  - On app load, fetch `/api/user-context/status`; if `needsOnboarding`, show onboarding UI.
  - **OnboardingView** (`ui/src/components/assistant-ui/onboarding.tsx`): form (personality, goals, experience level), Submit and Skip; on success calls `onComplete()` so the app shows the chat.
  - **App.tsx**: state `needsOnboarding` (null = loading); renders loading, `OnboardingView`, or main chat accordingly.

### 5. Documentation

- **.agents/project-context.md**: directory structure updated with `user_context/`, `user_context_store.py`, `user_context_loader.py`; new subsection "User context workspace (Phase 1)" (layout and skill convention).
- **planning/comfyui_assistant_development_phases.md**: note under Phase 1 that implementation details and skill layout are in project-context; Phase 3 will use the same `user_context/skills/` layout.
- **user_context/README.md**: short guide to the workspace and skill file format (for users editing the folder).
- **.gitignore**: `user_context/context.db`, `user_context/SOUL.md`, `user_context/goals.md`, `user_context/skills/*.md` (user data not committed).

---

## File and route summary

| Item | Location / path |
|------|------------------|
| User context path | `__init__.py`: `user_context_path`, `user_context_store.set_user_context_path()` |
| Store | `user_context_store.py` |
| Loader | `user_context_loader.py` |
| Prompt formatting | `agent_prompts.py`: `format_user_context()`, `get_system_message(user_context=None)` |
| Chat handler | `__init__.py`: `chat_api_handler` (loads context, passes to `get_system_message`) |
| Status endpoint | GET `/api/user-context/status` → `user_context_status_handler` |
| Onboarding endpoint | POST `/api/user-context/onboarding` → `user_context_onboarding_handler` |
| Onboarding UI | `ui/src/components/assistant-ui/onboarding.tsx` |
| App gate | `ui/src/App.tsx`: fetch status, show onboarding or `AppContent` |

---

## Iteration log

*(Add short entries here when changing Phase 1 behaviour or layout.)*

- **Initial implementation**: Workspace, SQLite store, SOUL/goals/skills loading, prompt injection, onboarding (backend + frontend), docs and README.
- **System context from .md**: Base prompt moved from `agent_prompts.py` string constants to `system_context/*.md` (01_role_and_capabilities.md, 02_tool_guidelines.md, 03_node_reference.md). Context assembly is now **system_context + user_context + skills** via the same loader mechanism. `agent_prompts.py` only provides `format_user_context()` and `get_system_message(system_context_text, user_context)`.
