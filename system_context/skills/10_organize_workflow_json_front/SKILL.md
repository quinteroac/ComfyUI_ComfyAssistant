---
name: organize-workflow-json-front
description: When the user asks to organize a workflow, read frontend JSON, reorganize for readability, apply in a new tab, and always validate with getWorkflowInfo. Run automatically without asking.
---

# Organize Workflow JSON (Frontend)

When the user asks to organize a workflow, follow this flow. Do not ask for confirmation; run it automatically.

1. **Read the workflow** from the canvas as full frontend JSON. Call **getWorkflowInfo** with **fullFormat: true** and use the `fullWorkflow` (or `fullWorkflowRef` / `_tempFile` if the response points to a temp file) from the response.

2. **Reorganize layout and readability only** — do not change logic. Keep node IDs, node types, widgets, links, and parameters unchanged.

3. **Organization rules:**
   - Main flow left-to-right by dependency.
   - **Use the frontend format’s `groups`** (ComfyUI API) to group by stage (e.g. load/model, conditioning, sampling, decode, output). `groups` is an array of objects with `id` (optional), `title`, `bounding` (tuple `[x, y, w, h]`), and optional `color`, `font_size`, `locked`. Nodes can reference a group via `parentId`.
   - Align columns and rows with consistent spacing.
   - Minimize crossing and long cables.
   - Separate auxiliary branches.
   - Keep reroutes only when they improve clarity.

4. **Output** must be frontend JSON (`nodes` + `links`, and `groups` when applicable). Do **not** use the API format (`class_type` / `inputs` keyed by node IDs).

5. **Apply** the result with **applyWorkflowJson** using the reorganized frontend JSON. The tool applies in a new tab. Do not ask the user or request confirmation.

6. **Mandatory final validation (do not skip):** Right after applying, **always** run **getWorkflowInfo** to validate the applied workflow. Check: same number of nodes and links as applied, groups present if you defined them, no errors in the response. If anything is wrong (missing nodes, broken links, inconsistent groups), fix it (adjust JSON and re-apply with **applyWorkflowJson**, or use the appropriate tools), then **validate again** until the state is correct. The flow is not complete until this validation has been run and the result is correct.

7. **Run the full flow automatically:** read → reorganize → apply → **always validate** (and correct if needed). Do not consider the task done without having run the validation in step 6.
