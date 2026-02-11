---
name: workflow-guardrails
description: Decision order and safety checks for user workflow requests to prevent hallucinated or invalid workflows.
---

# Workflow guardrails (required for workflow requests)

When the user asks to **create or provide a complete workflow**, follow this exact decision order:

1. **Do I already have a skill for this workflow?**
   - If yes: use that skill's instructions.
   - If no: continue.

2. **Am I confident I know how to build this workflow?**
   - Only answer "yes" if you are certain and can name the required nodes and models without guessing.
   - If yes: proceed, but you still **must validate availability** (see step 4) before applying anything.
   - If no: continue.

3. **Check local ComfyUI_examples references first** (use `getExampleWorkflow`).
   - If a matching example exists, use it and continue to validation.
   - If not found, continue.
   - When matching nodes inside the example workflow, use **display titles** (from `titleTypeMap`) as the primary lookup key.

4. **Search the web for a known workflow** using `webSearch`.
   - For promising results, **always call `fetchWebContent`** to verify and extract the workflow details.
   - If a workflow is found and verified: continue.
   - If not found: **ask the user what they want to do** (clarify goals, ask for a reference, or suggest alternatives).

5. **Validate requirements** (nodes and models).
   - Use `searchInstalledNodes` and `getAvailableModels`.
    - This validation is **required even if you are confident** you know the workflow.
   - Use the model-loading-rules skill to choose Load Diffusion Model vs CheckpointLoaderSimple based on model location.
   - If required nodes/models are missing: **tell the user what is missing** and **suggest what to install or select**.
   - If everything is available: continue.

6. **Apply the workflow** with `applyWorkflowJson`.

## Non-negotiable safety rules

- **Never guess** node types or model filenames.
- **Never hallucinate** a workflow when you are unsure.
- **If you did not verify a workflow**, you must not apply one.
- **Ask for clarification** instead of inventing steps.
- **Default to JSON** for complete workflows; use `addNode` only when explicitly requested.
