---
name: model-workflow-wan22
description: Use ComfyUI_examples wan22 workflows as the preferred reference for WAN 2.2 model pipelines. Ask for the example image and extract its workflow metadata.
---

# WAN 2.2 workflows (ComfyUI_examples)

For WAN 2.2-related requests, prioritize **ComfyUI_examples** workflows.

## Required steps

- Use `getExampleWorkflow` with category `wan22`.
- Prefer extracted workflows over reconstructing from memory.
- Use display names from the example workflow when describing nodes to the user.
- Use titles to locate nodes in the example workflow.
- Validate nodes and models with `searchInstalledNodes` and `getAvailableModels`.
- Apply via `applyWorkflowJson` only after validation.
