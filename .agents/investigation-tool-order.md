# Investigation: Model ignores tool usage rules

**Date**: 2026-02-13
**Status**: Pending investigation

## Problem

The LLM is not following the tool usage order defined in the system prompt skills. Instead of using `applyWorkflowJson` for complete workflows, it builds them node-by-node with `addNode`/`connectNodes`/`setNodeWidgetValue`/`fillPromptNode`.

## Evidence (from `user_context/logs/chat_2026-02-13.jsonl`)

Conversation: user asks to create an Anima Preview workflow ("si porfavor", lines 4–9).

### What the model did (~28 tool calls across 6 rounds):

1. `searchInstalledNodes` — OK
2. `getAvailableModels` — OK
3. 7x `addNode` (with position param) — WRONG
4. 7x `setNodeWidgetValue` — unnecessary if using JSON
5. 9x `connectNodes` — unnecessary if using JSON
6. 2x `fillPromptNode` — unnecessary if using JSON

### What it should have done (~3-4 tool calls in 2-3 rounds):

1. `getUserSkill("anima-preview")` — user skill exists and was not consulted
2. `searchInstalledNodes` + `getAvailableModels` — validate
3. `applyWorkflowJson` — single call with complete workflow

## Rules violated

### `07_workflow_guardrails/SKILL.md`
- **Line 10-13**: Decision order step 1 — "Do I already have a skill for this workflow? If yes: use that skill's instructions." → User skill `anima-preview` exists but was never loaded.
- **Line 44**: "Default to JSON for complete workflows; use addNode only when explicitly requested."

### `05_workflow_execution/SKILL.md`
- **Line 40-42**: "Prefer applyWorkflowJson for any complete workflow request, even if the workflow is small. Use JSON-first. Only use addNode/connectNodes if the user explicitly asks for step-by-step."
- **Line 46-48**: "Always call searchInstalledNodes first... Always call getAvailableModels... Never guess model filenames." → Model did validate, but then didn't use `applyWorkflowJson`.

### `01_base_tools/SKILL.md`
- **Line 39**: "Do NOT specify position parameter — the system will automatically position nodes." → Model passed `position` to every `addNode` call.
- **Line 68**: "For complete workflows — use applyWorkflowJson unless the user explicitly asks for step-by-step."

### `02_tool_guidelines/SKILL.md`
- **Line 10**: "Check if similar nodes already exist (use getWorkflowInfo)" → Model never called `getWorkflowInfo` before adding nodes.

## Next steps to investigate

1. **How is the system prompt assembled?** Trace `load_system_context()` → `get_system_message()` → API call. Check skill loading order and whether all skills are included.

2. **Is there truncation?** Check if `_truncate_chars` or other limits are cutting off `workflow_guardrails` or `workflow_execution` skills before they reach the model.

3. **Skill ordering**: Skills are numbered 01–17. Check if later skills (05, 07) get lower priority or are truncated. The guardrails (07) and execution (05) skills contain the critical rules being ignored.

4. **Continuation turns**: After the first message, `get_system_message_continuation()` sends only a short message: "Continue the conversation. Apply the same rules..." — the model may lose awareness of specific rules on tool-use rounds 2+.

5. **Prompt reinforcement**: Consider whether critical rules like "use applyWorkflowJson for complete workflows" need to be in `01_role.md` (always first) rather than buried in skill 05/07.

6. **User skill awareness**: The model had `anima-preview` listed in user skills but never called `getUserSkill`. Check if the skills index is visible in the system message and if the guardrails decision order is prominent enough.

## Findings so far

- System context is assembled by `user_context_loader.load_system_context()` by concatenating every top-level markdown file and the numbered skills under `system_context/skills` in sorted order. `agent_prompts.get_system_message()` wraps that output with the skills index, rules, and environment summary, then `__init__.py` prepends the result to the first API turn after `_smart_truncate_system_context()` compresses or drops late sections; the guardrail skills therefore land in the initial system prompt but may not survive aggressive truncation if the budget is exceeded.
- Subsequent turns reuse `agent_prompts.get_system_message_continuation()`, which only contains the generic reminder “continue and apply the same rules” plus the user skills/environment summaries; it does not re-state the workflow guardrails, JSON-first requirement, or the need to call `getUserSkill` before building a workflow. That lack of explicit reinforcement lets the LLM forget the order when it issues tool calls after the first turn even though the initial prompt included everything.
- Key rules (skills 05 and 07) are not duplicated in `01_role.md`, so any truncation or omission of the later skill sections removes the most actionable guidance. The guardrails therefore need a more persistent anchor than a single first message.

## Actions taken

- Added a workflow guardrails reminder to `agent_prompts.get_system_message_continuation()` so every turn explicitly reiterates the skill lookup → validation → JSON-first guidance, keeping those rules available even when the rest of the system context has been truncated or omitted.

## Files to review

- `user_context_loader.py` — how system_context skills are loaded and ordered
- `__init__.py` — where `get_system_message()` is called and how context is assembled for the API
- `agent_prompts.py` — `get_system_message()` and `get_system_message_continuation()`
- `system_context/` — skill loading order (numbered prefixes)
- Check for any `max_chars` / truncation applied to the assembled system message
