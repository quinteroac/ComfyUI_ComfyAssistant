---
name: comfyui-examples-source
description: Use ComfyUI_examples as the first source of truth for complete workflows. Prefer extracting workflows from example images and validating nodes/models before applying.
---

# ComfyUI_examples is the first source for workflows

When the user asks for a complete workflow, **first consult the ComfyUI_examples repo**:

`https://github.com/comfyanonymous/ComfyUI_examples`

This repo’s example images include embedded workflow metadata. Some folders also include JSON workflow files. Use it as the **primary reference** for known workflows before inventing or assembling one yourself.

## Required behavior

- **Use `getExampleWorkflow`** to query the local extracted references in `system_context/skills/08_comfyui_examples_source/references/`.
- **Prefer extraction** of embedded workflow metadata or JSON files over manual reconstruction.
- **Use display names** from the example workflow (titles) when describing nodes to the user.
- **Use titles to locate nodes** when matching or searching for nodes in the example workflow.
- **Validate nodes and models** with `searchInstalledNodes` and `getAvailableModels` before applying.
- If no suitable example exists locally, follow workflow-guardrails and research-tools steps.
