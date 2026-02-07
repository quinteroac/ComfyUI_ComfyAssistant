---
name: tool-guidelines
description: Guidelines for using graph tools (before adding nodes, connecting, error handling, multi-step operations).
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

## Error Handling

- If getWorkflowInfo returns empty, the workflow is blank
- If addNode fails, the node type might be invalid
- If connectNodes fails, check slot indices and node IDs
- If removeNode fails, the node might not exist

## Multi-Step Operations

For complex requests, break them down:

1. Explain your plan
2. Execute steps one by one
3. Verify each step succeeded
4. Summarize what was accomplished
