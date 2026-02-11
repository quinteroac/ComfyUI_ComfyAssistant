---
name: model-workflow-qwen-image
description: Use ComfyUI_examples qwen_image workflows as the preferred reference for Qwen Image model pipelines. Ask for the example image and extract its workflow metadata.
---

# Qwen Image workflows (ComfyUI_examples)

For Qwen Image-related requests, prioritize **ComfyUI_examples** workflows.

## Required steps

- Use `getExampleWorkflow` with category `qwen_image`.
- Prefer extracted workflow metadata over reconstructing from memory.
- Use display names from the example workflow when describing nodes to the user.
- Use titles to locate nodes in the example workflow.
- Validate nodes and models with `searchInstalledNodes` and `getAvailableModels`.
- Apply via `applyWorkflowJson` only after validation.
