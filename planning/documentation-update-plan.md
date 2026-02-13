# Documentation Update Plan

**Purpose**: Resolve discrepancies between documentation and code identified in the doc-vs-code audit.  
**Audience**: Contributors and agents updating project docs.  
**Status**: Draft — tasks to be executed in order.

---

## Summary of Discrepancies

| Area | Count | Main issues |
|------|--------|-------------|
| Tools | 2 | New tools `searchTemplates`, `applyTemplate` not documented |
| Directory structure & skills | 9+ | Missing dirs in tree; wrong skill counts; new files not listed |
| Environment variables | 8 | New/optional vars not in project-context |
| API endpoints | 1 | `POST /api/research/examples` not documented |
| Versions | 1 | `ui/package.json` 0.1.0 vs `pyproject.toml` 0.2.0 |

---

## Phase 1: Tools (High priority)

**Goal**: Available Tools list in project-context matches backend and frontend.

### Task 1.1 — Add missing tools to project-context

**File**: `.agents/project-context.md`  
**Section**: "Available Tools:" (around line 177).

**Action**: Append these two bullets after `searchNodeRegistry`:

```markdown
- `searchTemplates`: Search official and community workflow templates by title, description, or category (e.g. wan, flux). Use to find a starting point for complex workflows.
- `applyTemplate`: Download and apply a selected workflow template to the canvas. Replaces the current graph.
```

**Check**: Grep for `searchTemplates` and `applyTemplate` in `tools_definitions.py` and `ui/src/tools/` to confirm names and descriptions align.

---

## Phase 2: Directory structure and skills (High priority)

**Goal**: Directory tree and skill lists in project-context reflect the repo on disk.

### Task 2.1 — Update system_context/skills in directory tree

**File**: `.agents/project-context.md`  
**Section**: Directory Structure (lines ~79–86).

**Current** (only 01–06 listed):

```
│   │   ├── 01_base_tools/SKILL.md
│   │   ├── 02_tool_guidelines/SKILL.md
│   │   ├── 03_node_reference/SKILL.md
│   │   ├── 04_environment_tools/SKILL.md
│   │   ├── 05_workflow_execution/SKILL.md
│   │   └── 06_research_tools/SKILL.md
```

**Action**: Replace with the full list present on disk (add 07, 08, 09, 17; do not re-add deleted 09–16 model skills):

```
│   │   ├── 01_base_tools/SKILL.md
│   │   ├── 02_tool_guidelines/SKILL.md
│   │   ├── 03_node_reference/SKILL.md
│   │   ├── 04_environment_tools/SKILL.md
│   │   ├── 05_workflow_execution/SKILL.md
│   │   ├── 06_research_tools/SKILL.md
│   │   ├── 07_workflow_guardrails/SKILL.md
│   │   ├── 08_comfyui_examples_source/SKILL.md
│   │   ├── 09_template_library/SKILL.md
│   │   └── 17_model_loading_rules/SKILL.md
```

**Note**: Skills 10–16 (model-specific) were removed; do not document them.

### Task 2.2 — Update .agents/ in directory tree

**File**: `.agents/project-context.md`  
**Section**: Directory Structure (lines ~67–77).

**Action**:

1. Change "8 skill modules" to "15 skill modules" (or "agent skill modules" and list count).
2. Add the missing skill directories to the list:
   - `architecture-overview/`
   - `backend-architecture/`
   - `backend-tools-declaration/`
   - `documentation/`
   - `environment-and-models/`
   - `patterns-and-conventions/`
   - `system-and-user-context/`
   - `ui-integration/`
3. Optionally add a line for ad-hoc agent notes, e.g.:
   - `.agents/*.md` — Agent investigation or one-off notes (e.g. `investigation-tool-order.md`).

### Task 2.3 — Update user_context in directory tree

**File**: `.agents/project-context.md`  
**Section**: Directory Structure (lines ~89–99).

**Action**: Under `user_context/`, add:

```
│   └── logs/                   # Optional: daily JSONL conversation logs (when COMFY_ASSISTANT_ENABLE_LOGS=1)
```

### Task 2.4 — Add conversation_logger.py to directory tree

**File**: `.agents/project-context.md`  
**Section**: Directory Structure (root-level Python files, lines ~117–124).

**Action**: Add `conversation_logger.py` to the list (e.g. after `documentation_resolver.py`), with a short comment: "Conversation logging to user_context/logs/ (optional)."

### Task 2.5 — Update "Skills System (.agents/)" list

**File**: `.agents/project-context.md`  
**Section**: "Skills System (.agents/)" (around lines 380–392).

**Action**: Replace the bullet list of skills with the 15 actual modules (or a "see directory structure" pointer and the full list). Ensure these are present: architecture-overview, assistant-ui, backend-architecture, backend-tools-declaration, documentation, environment-and-models, patterns-and-conventions, primitives, runtime, setup, streaming, system-and-user-context, thread-list, tools, ui-integration.

---

## Phase 3: Environment variables (Medium priority)

**Goal**: All env vars read by the backend and present in `.env.example` are documented in project-context.

### Task 3.1 — Extend Environment Variables section

**File**: `.agents/project-context.md`  
**Section**: "Environment Variables" → "Backend (.env)" (lines ~263–284).

**Action**: After the existing block (ending with `COMFY_ASSISTANT_DEBUG_CONTEXT=0`), add the following (to match `.env.example` and code):

```bash
COMFY_ASSISTANT_LOG_LEVEL=INFO           # Optional: DEBUG, INFO, WARNING, ERROR. Default: INFO
COMFY_ASSISTANT_ENABLE_LOGS=0             # Optional: when "1", save conversation logs to user_context/logs/
LLM_REQUEST_DELAY_SECONDS=1.0            # Optional: delay before each LLM request (avoid 429)
LLM_SYSTEM_CONTEXT_MAX_CHARS=12000       # Optional: max chars from system_context per request
LLM_USER_CONTEXT_MAX_CHARS=2500          # Optional: max chars for user context block
LLM_HISTORY_MAX_MESSAGES=24              # Optional: max non-system messages per request
LLM_TOOL_RESULT_KEEP_LAST_ROUNDS=2       # Optional: full tool-result rounds kept; older get placeholder
```

**Note**: `ANTHROPIC_AUTH_TOKEN` is not used by this backend (Anthropic uses `ANTHROPIC_API_KEY`). If mentioned in code comments, add a single line in docs: "ANTHROPIC_AUTH_TOKEN is for Claude Code CLI only; this backend uses ANTHROPIC_API_KEY."

---

## Phase 4: API endpoints (Medium priority)

**Goal**: All research-related endpoints are documented.

### Task 4.1 — Document POST /api/research/examples

**File**: `.agents/project-context.md`  
**Section**: "Phase 8 API Endpoints" table (lines ~372–378).

**Action**: Add one row:

| `/api/research/examples` | POST | Fetch example workflows by category (e.g. from ComfyUI_examples) |

Ensure the table still lists `/api/research/search`, `/api/research/fetch`, `/api/research/registry` as they are.

---

## Phase 5: Version consistency (Low priority)

**Goal**: Single source of truth for version; docs state the rule.

### Task 5.1 — Align frontend version with backend

**File**: `ui/package.json`.

**Action**: Set `version` to `"0.2.0"` so it matches `pyproject.toml` (if the project decision is to keep 0.2.0 as the release version).

**Alternative**: If the UI is intentionally versioned separately, document that in project-context (e.g. "Frontend version in ui/package.json may differ; release version is in pyproject.toml.").

### Task 5.2 — Document versioning rule (optional)

**File**: `.agents/project-context.md` or `.agents/conventions.md`.

**Action**: Add a short note: "Release version is defined in pyproject.toml; ui/package.json should be kept in sync for releases."

---

## Execution checklist

Use this to track progress. Complete Phase 1 before Phase 2, etc.

- [ ] **Phase 1**
  - [ ] 1.1 Add `searchTemplates` and `applyTemplate` to Available Tools
- [x] **Phase 2**
  - [x] 2.1 Update system_context/skills list (07, 08, 09, 17; no 10–16)
  - [x] 2.2 Update .agents/ skill count and list (15 modules + optional *.md)
  - [x] 2.3 Add user_context/logs/ to tree
  - [x] 2.4 Add conversation_logger.py to tree
  - [x] 2.5 Update "Skills System (.agents/)" list
- [x] **Phase 3**
  - [x] 3.1 Document new/optional env vars (log level, logs, delay, context/history limits)
- [ ] **Phase 4**
  - [ ] 4.1 Add POST /api/research/examples to Phase 8 table
- [ ] **Phase 5**
  - [ ] 5.1 Set ui/package.json version to 0.2.0 (or document divergence)
  - [ ] 5.2 (Optional) Document versioning rule

---

## After completion

1. Run a quick sanity check: search for "searchTemplates", "applyTemplate", "09_template_library", "conversation_logger", "COMFY_ASSISTANT_ENABLE_LOGS", "/api/research/examples" in `.agents/project-context.md` and ensure they appear where expected.
2. If any new tools or endpoints are added later, update this plan or the checklist and keep project-context in sync (see `.agents/conventions.md` — Documentation Maintenance Protocol).
