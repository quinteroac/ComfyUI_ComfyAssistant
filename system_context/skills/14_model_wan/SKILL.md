---
name: model-workflow-wan
description: Use ComfyUI_examples wan workflows as the preferred reference for WAN model pipelines. Ask for the example image and extract its workflow metadata.
---

# WAN workflows (ComfyUI_examples)

For WAN-related requests, prioritize **ComfyUI_examples** workflows.

## Required steps

- Use `getExampleWorkflow` with category `wan`.
- Prefer extracted workflows over reconstructing from memory.
- Use display names from the example workflow when describing nodes to the user.
- Use titles to locate nodes in the example workflow.
- Validate nodes and models with `searchInstalledNodes` and `getAvailableModels`.
- Apply via `applyWorkflowJson` only after validation.
