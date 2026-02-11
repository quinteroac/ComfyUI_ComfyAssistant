---
name: model-workflow-z-image
description: Use ComfyUI_examples z_image workflows as the preferred reference for Z-Image model pipelines. Ask for the example image and extract its workflow metadata.
---

# Z-Image workflows (ComfyUI_examples)

For Z-Image-related requests, prioritize **ComfyUI_examples** workflows.

## Required steps

- Use `getExampleWorkflow` with category `z_image`.
- Prefer extracted workflow metadata over reconstructing from memory.
- Use display names from the example workflow when describing nodes to the user.
- Use titles to locate nodes in the example workflow.
- Validate nodes and models with `searchInstalledNodes` and `getAvailableModels`.
- Apply via `applyWorkflowJson` only after validation.
