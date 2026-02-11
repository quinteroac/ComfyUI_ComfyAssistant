---
name: model-workflow-flux
description: Use ComfyUI_examples flux workflows as the preferred reference for Flux model pipelines. Ask for the example image and extract its workflow metadata.
---

# Flux workflows (ComfyUI_examples)

For Flux-related requests, prioritize **ComfyUI_examples** workflows.

## Required steps

- Use `getExampleWorkflow` with category `flux`.
- Prefer extracted workflow metadata over reconstructing from memory.
- Use display names from the example workflow when describing nodes to the user.
- Use titles to locate nodes in the example workflow.
- Validate nodes and models with `searchInstalledNodes` and `getAvailableModels`.
- Apply via `applyWorkflowJson` only after validation.
