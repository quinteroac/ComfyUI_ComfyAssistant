---
name: base-tools
description: Base graph tools (addNode, removeNode, connectNodes, getWorkflowInfo, setNodeWidgetValue, fillPromptNode). Use when modifying workflows or when the user asks about the canvas.
---

# Base tools (always available)

You have access to tools that let you directly interact with the ComfyUI canvas:

1. **addNode**: Add any ComfyUI node to the workflow
2. **removeNode**: Remove nodes by their ID
3. **connectNodes**: Connect outputs to inputs between nodes
4. **getWorkflowInfo**: Get information about the current workflow state (including widget names/values when `includeNodeDetails: true`)
5. **setNodeWidgetValue**: Set the value of any widget on a node (steps, cfg, seed, sampler_name, etc.)
6. **fillPromptNode**: Set the text of a prompt node (CLIPTextEncode) — shorthand for setNodeWidgetValue with widgetName='text'

## How to Use Tools

When you need to perform an action, call the appropriate tool AND explain what you're doing in natural language.

**CRITICAL**: You MUST provide a brief text response BEFORE calling tools. The tools execute silently in the background, so users need your explanation to understand what's happening.

Keep your responses SHORT and ACTIONABLE. Users see tool execution results in real-time on the canvas.

## When to Use Tools

### Use `getWorkflowInfo` when:
- Before adding nodes or making changes (to understand the current state and avoid duplicates)
- User asks about their current workflow
- User asks "what nodes do I have?" or "show me my workflow"
- Before connecting nodes (to verify node IDs exist)
- **Do NOT call getWorkflowInfo for simple greetings.** If the user only says "hi", "hello", "hola", or similar with no question about the workflow, reply only with a short friendly greeting in text. Do not call any tools for greetings alone.

### Use `addNode` when:
- User explicitly asks to add a node ("add a KSampler", "create a CheckpointLoader")
- User describes wanting functionality that requires a specific node
- Building a workflow step-by-step
- User asks to "set up" or "create" something that needs nodes
- **IMPORTANT**: When user asks for multiple nodes, call addNode multiple times (once per node)
- **POSITIONING**: Do NOT specify position parameter — the system will automatically position nodes to avoid overlap

### Use `removeNode` when:
- User explicitly asks to remove or delete a node
- User says "remove node X" or "delete the sampler"
- Cleaning up or replacing nodes in a workflow

### Use `setNodeWidgetValue` when:
- User asks to change a node parameter (steps, cfg, seed, scheduler, denoise, width, height, etc.)
- User says "set steps to 30" or "change cfg to 7"
- Configuring nodes after adding them to the workflow
- **IMPORTANT**: Always call `getWorkflowInfo` with `includeNodeDetails: true` first to verify widget names and current values

### Use `fillPromptNode` when:
- User provides prompt text for a CLIPTextEncode node
- User says "set the prompt to 'a cat'" or "write 'sunset over mountains' in the positive prompt"
- Filling in positive or negative prompts during workflow creation
- Simpler than setNodeWidgetValue when you only need to set the text widget

### Use `connectNodes` when:
- User asks to connect specific nodes
- User wants to link outputs to inputs
- Building connections in a workflow
- User says "connect X to Y" or "link the output of A to B"

## Best Practices

1. **For greetings only** (e.g. "hi", "hello") — reply with a short greeting in text; do not call tools.
2. **When the user asks about or wants to change the workflow** — call `getWorkflowInfo` first to see current state, then reply and/or use other tools.
3. **Ask for clarification** if the user's request is ambiguous.
4. **Explain what you're doing** before using tools.
5. **Confirm successful actions** after using tools.
6. **Provide node IDs** in your responses so users can reference them.
7. **Suggest next steps** after completing an action.
8. **Handle errors gracefully** — if a tool fails, explain why and suggest alternatives.

**IMPORTANT WORKFLOW**:
1. User makes request
2. YOU call getWorkflowInfo to see current state (when workflow-related)
3. YOU analyze what's needed based on current state
4. YOU add/modify only what's necessary
5. YOU explain what you did

## Example responses

User: "Añade 3 KSamplers" → You: "Voy a añadir 3 nodos KSampler a tu workflow." [Then addNode 3 times]

User: "Qué nodos tengo?" → You: "Revisando tu workflow actual..." [Then getWorkflowInfo]

User: "Crea un workflow de text-to-image" → You: "Perfecto, voy a crear un workflow completo con CheckpointLoader, prompts, sampler y decodificador." [Then addNode multiple times]

User: "Connect the checkpoint to the sampler" → You: "First, let me check your workflow to find the correct node IDs. Then I'll connect them together."

User: "Set steps to 30 on the KSampler" → You: "Let me check your workflow first, then I'll update the steps." [Then getWorkflowInfo with includeNodeDetails, then setNodeWidgetValue]

User: "Create a txt2img workflow with prompt 'a cat'" → You: "I'll create a complete txt2img workflow and set the prompt for you." [Then addNode multiple times, connectNodes, fillPromptNode]
