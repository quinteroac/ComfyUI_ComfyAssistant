---
name: model-workflow-flux2
description: Use ComfyUI_examples flux2 workflows as the preferred reference for Flux2 model pipelines. Ask for the example image and extract its workflow metadata.
---

# Flux2 workflows (ComfyUI_examples)

For Flux2-related requests, prioritize **ComfyUI_examples** workflows.

## Required steps

- Use `getExampleWorkflow` with category `flux2`.
- Prefer extracted workflow metadata over reconstructing from memory.
- Use display names from the example workflow when describing nodes to the user.
- Use titles to locate nodes in the example workflow.
- Validate nodes and models with `searchInstalledNodes` and `getAvailableModels`.
- Apply via `applyWorkflowJson` only after validation.
