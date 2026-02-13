# Base tools

The assistant controls your ComfyUI workflow through **tools** that run in the browser and act on the graph. You do not call these tools yourself; you ask in **natural language** and the assistant chooses when to use each tool.

This page describes what the assistant can do (the "base tools") and how you can ask for it.

## What the assistant can do

| Tool | What it does |
|------|----------------|
| **addNode** | Add a node to the canvas by type (e.g. KSampler, CheckpointLoader, CLIPTextEncode, PreviewImage). |
| **removeNode** | Remove a node by ID. |
| **connectNodes** | Connect an output of one node to an input of another (by node IDs and slot names). |
| **getWorkflowInfo** | Get the list of nodes and connections; optionally include widget names and values for each node. |
| **setNodeWidgetValue** | Set any widget on a node (steps, cfg, seed, sampler_name, scheduler, denoise, width, height, etc.). |
| **fillPromptNode** | Set the text of a prompt node (CLIPTextEncode) — the assistant uses this for positive/negative prompts. |
| **refreshEnvironment** | Rescan the ComfyUI installation to update the list of installed nodes, packages, and models. |
| **searchInstalledNodes** | Search installed node types by name, category, package, display name, or description. Uses cache first; if no results, queries ComfyUI's node API. |
| **getAvailableModels** | List installed model filenames by category (checkpoints, loras, vae, etc.). Use when asking for model recommendations (e.g. "I want hyperrealistic, what do you recommend?"). |
| **readDocumentation** | Fetch documentation for a node type, package, or topic. |
| **createSkill** | Create a persistent user skill (remembered instruction or preference) that the assistant will follow in future conversations. |
| **deleteSkill** | Delete a user skill by its slug (e.g. when the user says "forget that" or "remove that preference"). |
| **updateSkill** | Update an existing skill's name, description, or instructions by slug. |
| **getUserSkill** | Fetch a user skill's full instructions by slug (on demand; used when the user refers to a skill). |
| **listUserSkills** | List all user skills with name, description, and slug. |
| **listSystemSkills** | List model-specific system skills (e.g. Flux, SDXL) available on demand. |
| **getSystemSkill** | Fetch a model-specific system skill's instructions by slug (on demand). |
| **executeWorkflow** | Queue the current workflow and wait for completion; returns status and output summary (images, errors, timing). |
| **applyWorkflowJson** | Load a complete API-format workflow, replacing the current graph. |
| **getExampleWorkflow** | Fetch example workflows extracted from ComfyUI_examples by category. |
| **webSearch** | Search the web for ComfyUI resources, tutorials, workflows. |
| **fetchWebContent** | Fetch and extract content from a URL; can detect embedded workflows. |
| **searchNodeRegistry** | Search the ComfyUI Registry for custom node packages. |

The assistant uses **getWorkflowInfo** first when it needs to see the current workflow (e.g. to find node IDs before connecting or changing settings). It then uses **addNode**, **connectNodes**, **setNodeWidgetValue**, and **fillPromptNode** to build or modify the graph. **executeWorkflow** runs the queue; **applyWorkflowJson** loads a full workflow from JSON. **getUserSkill**, **listUserSkills**, **listSystemSkills**, and **getSystemSkill** load skills on demand when you refer to them. Research tools (**webSearch**, **fetchWebContent**, **searchNodeRegistry**, **getExampleWorkflow**) help discover resources and workflows.

---

## How to ask (natural language)

You can type in plain language. The assistant will interpret your intent and call the right tools. Examples:

### Adding nodes

- "Add a KSampler"
- "Create a CheckpointLoader and a CLIPTextEncode"
- "Add three KSampler nodes"
- "I need a Preview Image node"

### Removing nodes

- "Remove node 5"
- "Delete the KSampler"
- "Remove the last node I added"

### Connecting nodes

- "Connect the checkpoint to the sampler"
- "Connect the positive prompt to the CLIPTextEncode"
- "Link the model output of the loader to the KSampler"

The assistant will use **getWorkflowInfo** to find the correct node IDs and then **connectNodes** with the right slots.

### Configuring nodes (widgets)

- "Set steps to 30 on the KSampler"
- "Change cfg to 7"
- "Set the seed to 42"
- "Use Euler as the sampler and set denoise to 0.9"

The assistant will use **setNodeWidgetValue** (and may call **getWorkflowInfo** with node details to get widget names).

### Setting prompts

- "Set the prompt to 'a cat on a sofa'"
- "Put 'sunset over mountains' in the positive prompt"
- "Write 'blurry, low quality' in the negative prompt"

The assistant will use **fillPromptNode** on the corresponding CLIPTextEncode node.

### Workflow-level requests

- "What nodes do I have?"
- "Show me my workflow"
- "Create a basic text-to-image workflow"
- "Create a txt2img workflow with 20 steps and prompt 'a cat'"

For "what do I have?", the assistant uses **getWorkflowInfo** and summarizes. For "create a workflow", it will add the needed nodes, connect them, and optionally set steps and prompt with the other tools.

### Environment and discovery

- "What custom nodes do I have?"
- "Do I have any upscaling nodes?"
- "How do I use KSampler?"
- "What models are available?"
- "I want a hyperrealistic image, what do you recommend?"
- "Which checkpoint should I use for anime?"
- "Scan my environment"

The assistant will use **refreshEnvironment** to scan, **searchInstalledNodes** to find node types, **getAvailableModels** to list your installed models and recommend specific checkpoints/LoRAs, and **readDocumentation** to get details.

### Remembering preferences

- "Remember to always use Preview Image instead of Save Image"
- "From now on, use 30 steps by default"
- "Always use the DPM++ 2M sampler"

The assistant will use **createSkill** to save the preference. It will be applied in future conversations automatically.

### Forgetting or changing preferences

- "Forget the preference about Preview Image"
- "Remove the skill about 30 steps"
- "Update my 'Use Preview Image' skill to say 'Use Preview Image for all outputs'"

The assistant will use **deleteSkill** (with the skill's slug) to remove it, or **updateSkill** to change name, description, or instructions. To know the slug, the assistant may need to reason from the skill name (e.g. "Use Preview Image" → slug `use-preview-image`) or use **listUserSkills** if needed.

### Executing and loading workflows

- "Run the workflow"
- "Execute the queue"
- "Load this workflow: [paste JSON]"

The assistant uses **executeWorkflow** to queue and run the current graph, or **applyWorkflowJson** to load a complete workflow from API-format JSON.

### Research and discovery

- "Search for ComfyUI upscale workflows"
- "Fetch the content from this URL: ..."
- "What custom nodes are in the Registry for control net?"
- "Give me an example txt2img workflow"

The assistant uses **webSearch**, **fetchWebContent**, **searchNodeRegistry**, and **getExampleWorkflow** to find resources, tutorials, and example workflows.

---

## Best practices

1. **Be specific when you have many nodes**: e.g. "Set steps to 30 on the **second** KSampler" or "On the KSampler connected to the positive prompt".
2. **One main request per message**: For complex workflows, you can break into steps or ask for one big request; the assistant can do multiple tool calls in one turn.
3. **Confirm destructive actions**: The assistant is instructed to confirm before removing nodes. You can still say "Yes, remove it" to proceed.
4. **Mention node types or IDs if helpful**: If the assistant previously showed you node IDs, you can refer to them (e.g. "Set steps on node 7").

---

## Limits

- **Tools run in the browser** (graph tools): They only see what ComfyUI exposes via its frontend API (`window.app`). Custom nodes are supported as long as they are registered in your ComfyUI instance.
- **Workflow execution** is supported via **executeWorkflow** (queue and wait) and **applyWorkflowJson** (load full workflow from API-format JSON).

---

## Related

- [Configuration](configuration.md) — API and user context setup.
- [User skills](skills.md) — Custom rules (e.g. "always use Preview Image") that affect how the assistant uses these tools.
