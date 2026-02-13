---
name: workflow-guardrails
description: Decision order and safety checks for user workflow requests to prevent hallucinated or invalid workflows.
---

# Workflow guardrails (required for workflow requests)

When the user asks to **create or provide a complete workflow**, follow this exact decision order:

1. **Do I already have a skill for this workflow?**
   - If yes: use that skill's instructions.
   - If no: continue.

2. **Have I searched workflow templates and custom-node templates?**
   - Call `searchTemplates(query)` with the model name, desired task, or related keywords before touching the canvas or building nodes manually.
   - Review the results for official templates and custom-node templates (the tool returns both sources). If a template matches the user's request, call `applyTemplate` with the reported `id`, `source`, and `package`.
   - When a template mentions custom node packages, call `searchNodeRegistry` to confirm the package is installed, and tell the user which package to install if not.
   - After applying a template, inspect the returned `referencedModels` and immediately call `getAvailableModels()` to compare; if models are missing, explain what to download.
   - Only proceed to manual construction after verifying no suitable template exists or the user explicitly rejects using one.

3. **Am I confident I know how to build this workflow?**
   - Only answer "yes" if you are certain and can name the required nodes and models without guessing.
   - If yes: proceed, but you still **must validate availability** (see step 6) before applying anything.
   - If no: continue.

4. **Check local ComfyUI_examples references first** (use `getExampleWorkflow`).
   - If a matching example exists, use it and continue to validation.
   - If not found, continue.
   - When matching nodes inside the example workflow, use **display titles** (from `titleTypeMap`) as the primary lookup key.

5. **Search the web for a known workflow** using `webSearch`.
   - For promising results, **always call `fetchWebContent`** to verify and extract the workflow details.
   - If a workflow is found and verified: continue.
   - If not found: **ask the user what they want to do** (clarify goals, ask for a reference, or suggest alternatives).

6. **Validate requirements** (nodes and models).
   - Use `searchInstalledNodes` and `getAvailableModels`.
    - This validation is **required even if you are confident** you know the workflow.
   - Use the model-loading-rules skill to choose Load Diffusion Model vs CheckpointLoaderSimple based on model location.
   - If required nodes/models are missing: **tell the user what is missing** and **suggest what to install or select**.
   - If everything is available: continue.

7. **Apply the workflow** with `applyWorkflowJson`.

## Non-negotiable safety rules

- **Never guess** node types or model filenames.
- **Never hallucinate** a workflow when you are unsure.
- **If you did not verify a workflow**, you must not apply one.
- **Ask for clarification** instead of inventing steps.
- **Default to JSON** for complete workflows; use `addNode` only when explicitly requested.
