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

The assistant uses **getWorkflowInfo** first when it needs to see the current workflow (e.g. to find node IDs before connecting or changing settings). It then uses **addNode**, **connectNodes**, **setNodeWidgetValue**, and **fillPromptNode** to build or modify the graph.

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

---

## Best practices

1. **Be specific when you have many nodes**: e.g. "Set steps to 30 on the **second** KSampler" or "On the KSampler connected to the positive prompt".
2. **One main request per message**: For complex workflows, you can break into steps or ask for one big request; the assistant can do multiple tool calls in one turn.
3. **Confirm destructive actions**: The assistant is instructed to confirm before removing nodes. You can still say "Yes, remove it" to proceed.
4. **Mention node types or IDs if helpful**: If the assistant previously showed you node IDs, you can refer to them (e.g. "Set steps on node 7").

---

## Limits

- **No workflow execution**: The assistant cannot run the queue or execute the workflow; it only edits the graph and widget values.
- **No loading/saving .json**: The assistant cannot load or save workflow files (planned for a future phase).
- **Tools run in the browser**: They only see what ComfyUI exposes via its frontend API (`window.app`). Custom nodes are supported as long as they are registered in your ComfyUI instance.

---

## Related

- [Configuration](configuration.md) — API and user context setup.
- [User skills](skills.md) — Custom rules (e.g. "always use Preview Image") that affect how the assistant uses these tools.
