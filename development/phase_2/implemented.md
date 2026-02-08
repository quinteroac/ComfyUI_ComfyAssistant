# Phase 2 — Node Configuration and Prompt Application

## Status: Implemented

## Summary

Phase 2 adds the ability for the assistant to fully configure node widgets, enabling end-to-end workflow creation from a single natural-language request like "create a txt2img workflow with 20 steps and prompt 'a cat'."

## New Tools

### setNodeWidgetValue
- **Purpose**: Sets the value of any widget on a node (steps, cfg, seed, sampler_name, scheduler, denoise, width, height, etc.)
- **Parameters**: `nodeId` (number), `widgetName` (string), `value` (string | number | boolean)
- **Error handling**: Lists available widget names when the specified widget is not found

### fillPromptNode
- **Purpose**: Sets the text of a CLIPTextEncode (prompt) node
- **Parameters**: `nodeId` (number), `text` (string)
- **Implementation**: Thin wrapper around setNodeWidgetValue with `widgetName='text'`

## Enhanced Existing Tools

### getWorkflowInfo
- Now includes `widgets` array when `includeNodeDetails: true`
- Each widget: `{ name, type, value }`
- Button-type widgets are filtered out
- Fixed: `__init__.py` was missing the `includeNodeDetails` parameter declaration

## Files Changed

### New files (5)
- `ui/src/tools/definitions/set-node-widget-value.ts` — Zod schema
- `ui/src/tools/implementations/set-node-widget-value.ts` — Widget value setting logic
- `ui/src/tools/definitions/fill-prompt-node.ts` — Zod schema
- `ui/src/tools/implementations/fill-prompt-node.ts` — Prompt filling (delegates to setNodeWidgetValue)
- `development/phase_2/implemented.md` — This file

### Modified files (11)
- `ui/src/tools/implementations/get-workflow-info.ts` — Added WidgetInfo interface and widget population
- `ui/src/tools/definitions/index.ts` — Barrel exports for new tools
- `ui/src/tools/implementations/index.ts` — Barrel exports for new tools
- `ui/src/tools/index.ts` — Registered new tools in createTools()
- `__init__.py` — Added tool declarations + fixed getWorkflowInfo + updated fallback prompt
- `tools_definitions.py` — Added new tool declarations
- `system_context/skills/01_base_tools/SKILL.md` — Documented new tools and usage patterns
- `system_context/skills/02_tool_guidelines/SKILL.md` — Added widget and prompt guidelines
- `system_context/skills/03_node_reference/SKILL.md` — Added widget names reference and prompt guide
- `system_context/01_role.md` — Updated capabilities and base tools list
- `.agents/project-context.md` — Updated available tools list
- `.agents/skills/tools/SKILL.md` — Updated tools table and folder structure
