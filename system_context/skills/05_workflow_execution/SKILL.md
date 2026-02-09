---
name: workflow-execution
description: Workflow execution and complete workflow generation tools (executeWorkflow, applyWorkflowJson). Use when the user wants to run a workflow or build a complete workflow from a description.
---

# Workflow Execution and Generation

You have tools to run workflows and load complete workflows from JSON.

## Available tools

| Tool | When to use |
|------|-------------|
| **executeWorkflow** | When the user says "run", "execute", "generate", "queue", or wants to see results from their workflow. |
| **applyWorkflowJson** | When building a complex multi-node workflow that would take many addNode/connectNodes calls. Generates and loads the entire graph in one step. |

## When to use `executeWorkflow`

- User says "run the workflow", "execute it", "generate the image", "queue it"
- After building or modifying a workflow, when the user wants results
- Accepts an optional `timeout` (seconds, default 300)

### Result interpretation

- **success** — Execution completed. Mention the number of outputs and any image filenames.
- **error** — Execution failed. Explain the error (node type, message) and suggest fixes (check connections, missing models, etc.).
- **interrupted** — User or system cancelled the execution.
- **timeout** — Execution took too long. Suggest the user check ComfyUI's queue or increase the timeout.

## When to use `applyWorkflowJson`

- User asks for a complete workflow ("create a txt2img workflow", "build me an img2img pipeline with upscale")
- The workflow requires many nodes and connections that would be tedious with individual addNode/connectNodes calls
- User provides or describes a workflow they want loaded

### CRITICAL: Before generating a workflow

1. **Always call `searchInstalledNodes`** first to verify the node types you plan to use exist in the user's installation
2. **Always call `getAvailableModels`** to find actual model filenames (checkpoints, loras, vae)
3. **Never guess model filenames** — use the exact filenames from the user's installation
4. If a required node type is not installed, tell the user what custom node package to install

## ComfyUI API format specification

The `workflow` parameter is an object where:
- **Keys** are string node IDs (e.g. `"1"`, `"2"`, `"3"`)
- **Values** are node objects with:
  - `class_type` (string): The registered node type name (e.g. `"CheckpointLoaderSimple"`)
  - `inputs` (object): Node inputs — either scalar values or link references
  - `_meta` (object, optional): `{ "title": "Display Name" }`

### Input value types

- **Scalar**: Direct value — `"steps": 20`, `"text": "a cat"`, `"seed": 42`
- **Link**: Reference to another node's output — `["5", 0]` means "output index 0 from node 5"
  - First element: source node ID (string)
  - Second element: output slot index (number)

### Example: basic txt2img workflow

```json
{
  "1": {
    "class_type": "CheckpointLoaderSimple",
    "inputs": {
      "ckpt_name": "v1-5-pruned-emaonly.safetensors"
    },
    "_meta": { "title": "Load Checkpoint" }
  },
  "2": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "a beautiful sunset over the ocean, highly detailed, 4k",
      "clip": ["1", 1]
    },
    "_meta": { "title": "Positive Prompt" }
  },
  "3": {
    "class_type": "CLIPTextEncode",
    "inputs": {
      "text": "blurry, low quality, deformed, ugly, watermark",
      "clip": ["1", 1]
    },
    "_meta": { "title": "Negative Prompt" }
  },
  "4": {
    "class_type": "EmptyLatentImage",
    "inputs": {
      "width": 512,
      "height": 512,
      "batch_size": 1
    },
    "_meta": { "title": "Empty Latent" }
  },
  "5": {
    "class_type": "KSampler",
    "inputs": {
      "seed": 42,
      "steps": 20,
      "cfg": 7,
      "sampler_name": "euler",
      "scheduler": "normal",
      "denoise": 1,
      "model": ["1", 0],
      "positive": ["2", 0],
      "negative": ["3", 0],
      "latent_image": ["4", 0]
    },
    "_meta": { "title": "KSampler" }
  },
  "6": {
    "class_type": "VAEDecode",
    "inputs": {
      "samples": ["5", 0],
      "vae": ["1", 2]
    },
    "_meta": { "title": "VAE Decode" }
  },
  "7": {
    "class_type": "PreviewImage",
    "inputs": {
      "images": ["6", 0]
    },
    "_meta": { "title": "Preview Image" }
  }
}
```

### CheckpointLoaderSimple outputs

- Output 0: MODEL
- Output 1: CLIP
- Output 2: VAE

## Build-then-run pattern

After calling `applyWorkflowJson` to load a workflow, suggest running it with `executeWorkflow` if the user wants to see results. Example flow:

1. User: "Create a txt2img workflow with a cat prompt and run it"
2. Call `searchInstalledNodes` to verify node types
3. Call `getAvailableModels` to find a checkpoint
4. Call `applyWorkflowJson` with the complete workflow
5. Call `executeWorkflow` to run it
6. Report the results

## Guidelines

- **Prefer `applyWorkflowJson`** over multiple `addNode`/`connectNodes` calls when building workflows with 4+ nodes
- **Always verify node types and models first** — never generate a workflow with guessed node types or model filenames
- **Use `PreviewImage` instead of `SaveImage`** by default unless the user specifically asks to save
- **Set reasonable defaults**: steps=20, cfg=7, sampler_name="euler", scheduler="normal", denoise=1.0
- **Use random seeds**: use a random number for the seed so each generation is different
