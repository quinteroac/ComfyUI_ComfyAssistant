# Phase 4 — Workflow Execution and Complex Workflows

**Status**: Done
**Branch**: `feature/phase-4-workflow-execution`

## Deliverables

- **executeWorkflow** — Queue the current workflow, wait for completion via ComfyUI events, return status + output summary (images, errors, timing).
- **applyWorkflowJson** — Load a complete API-format workflow in one call, replacing the current graph. Pre-validates node types, ensures `_meta.title`.
- **System prompt skill** — LLM guidance for when/how to use both tools, API format specification, example workflow, build-then-run pattern.
- **Role update** — Added new capabilities and tools to the base tools list.

## New files

| File | Purpose |
|------|---------|
| `ui/src/tools/definitions/execute-workflow.ts` | Zod schema + definition for executeWorkflow |
| `ui/src/tools/implementations/execute-workflow.ts` | Event-driven execution monitoring (listen → queue → resolve) |
| `ui/src/tools/definitions/apply-workflow-json.ts` | Zod schema + definition for applyWorkflowJson |
| `ui/src/tools/implementations/apply-workflow-json.ts` | Validate node types + load via `app.loadApiJson` |
| `system_context/skills/05_workflow_execution/SKILL.md` | LLM guidance, API format spec, examples |
| `development/phase_4/implemented.md` | This file |

## Modified files

| File | Changes |
|------|---------|
| `tools_definitions.py` | Added `executeWorkflow` and `applyWorkflowJson` definitions (OpenAI format) |
| `ui/src/tools/definitions/index.ts` | Re-export 2 new definitions |
| `ui/src/tools/implementations/index.ts` | Re-export 2 new implementations |
| `ui/src/hooks/useComfyTools.ts` | Registered 2 new tools with `useAssistantTool` |
| `system_context/01_role.md` | Added new capabilities + tools to base tools list |
| `doc/roadmap.md` | Marked Phase 4 as Done |
| `.agents/project-context.md` | Updated tools list + features |

## Architecture notes

### executeWorkflow

1. Serializes graph via `app.graphToPrompt()`
2. Attaches event listeners (`executed`, `execution_success`, `execution_error`, `execution_interrupted`) **before** queueing — prevents race condition
3. Queues via `app.api.queuePrompt(0, promptData)` — returns `prompt_id`
4. Filters all events by `prompt_id` to ignore other executions
5. Cleanup removes all listeners + clears timeout in every exit path
6. Returns `{ status, promptId, executionTimeMs, outputs, error? }`

### applyWorkflowJson

1. Pre-validates node types against `LiteGraph.registered_node_types`
2. Ensures `_meta.title` defaults to `class_type` if missing
3. Loads via `app.loadApiJson(apiData, fileName)`
4. Refreshes canvas via `setDirtyCanvas(true, true)`
5. Returns `{ nodeCount, nodeTypes[], warnings? }`

## Iteration log

- Initial implementation with all planned features
- Prettier formatting applied
- `prefer-const` lint issue resolved with eslint-disable comment (variable must be declared before cleanup closure references it)
