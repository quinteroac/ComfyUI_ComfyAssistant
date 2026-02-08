---
name: tool-guidelines
description: Guidelines for using graph tools (before adding nodes, connecting, setting widgets, error handling, multi-step operations).
---

# Tool Usage Guidelines

## Before Adding Nodes

1. Check if similar nodes already exist (use getWorkflowInfo)
2. Consider workflow organization and positioning
3. Think about what connections will be needed next

## When Connecting Nodes

1. Verify both nodes exist (use getWorkflowInfo first)
2. Confirm the output/input types are compatible
3. Explain what the connection does

## Before Setting Widget Values

1. Call `getWorkflowInfo` with `includeNodeDetails: true` to see available widgets and their current values
2. Verify the widget name exists on the target node — the error message lists available widgets if you get the name wrong
3. Use the correct value type for the widget (number for steps/cfg/seed, string for sampler_name/scheduler/text)
4. For combo/dropdown widgets (like sampler_name, scheduler), use one of the valid option values

## When Filling Prompts

1. Use `fillPromptNode` for CLIPTextEncode nodes — it's simpler than setNodeWidgetValue
2. Positive prompts: describe what you want to see (subject, style, quality, lighting)
3. Negative prompts: describe what to avoid (e.g., "blurry, low quality, deformed")
4. If the user specifies both positive and negative prompts, use separate fillPromptNode calls for each CLIPTextEncode node

## Error Handling

- If getWorkflowInfo returns empty, the workflow is blank
- If addNode fails, the node type might be invalid
- If connectNodes fails, check slot indices and node IDs
- If removeNode fails, the node might not exist
- If setNodeWidgetValue fails, the widget name may be wrong — check the error for available widget names
- If fillPromptNode fails, the node may not have a 'text' widget — use setNodeWidgetValue with the correct widget name instead

## Multi-Step Operations

For complex requests, break them down:

1. Explain your plan
2. Execute steps one by one
3. Verify each step succeeded
4. Summarize what was accomplished
