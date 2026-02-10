# Adding and Modifying Tools

This is the step-by-step guide for the most common developer task: adding or modifying the tools that the LLM can use to interact with ComfyUI.

> **Agent skill**: For machine-optimized reference, see [`.agents/skills/backend-tools-declaration/SKILL.md`](../../.agents/skills/backend-tools-declaration/SKILL.md).

---

## Tool architecture overview

Tools are the mechanism that lets the LLM take actions in ComfyUI. They have two sides:

1. **Backend** (`tools_definitions.py`) -- Declares tools in OpenAI function calling format. The LLM only sees these definitions and uses them to decide what to call.
2. **Frontend** (`ui/src/tools/`) -- Defines Zod schemas for validation and implements the actual execution logic. When the LLM calls a tool, the frontend runs the implementation.

The flow is: **LLM decides to call a tool** → **backend streams the tool call as SSE** → **frontend validates and executes** → **result is appended to messages** → **agentic loop resubmits**.

Both sides must stay in sync: same tool names, same parameter names and types.

---

## Current tools

| Tool | Category | Description |
|------|----------|-------------|
| `addNode` | Graph | Add a node to the workflow |
| `removeNode` | Graph | Remove a node by ID |
| `connectNodes` | Graph | Connect two nodes by slot indices |
| `getWorkflowInfo` | Graph | Query workflow state and node details |
| `setNodeWidgetValue` | Graph | Set any widget value on a node |
| `fillPromptNode` | Graph | Set text on a CLIPTextEncode node (shorthand) |
| `createSkill` | Skills | Create a persistent user skill |
| `deleteSkill` | Skills | Delete a user skill by slug |
| `updateSkill` | Skills | Update a user skill |
| `refreshEnvironment` | Environment | Rescan nodes, packages, models |
| `searchInstalledNodes` | Environment | Search node types |
| `getAvailableModels` | Environment | List models by category |
| `readDocumentation` | Environment | Fetch docs for a topic |
| `executeWorkflow` | Execution | Queue workflow and wait for result |
| `applyWorkflowJson` | Execution | Load a complete API-format workflow |

### Tool categories

- **Graph tools** execute in the frontend against `window.app.graph`. They manipulate nodes, connections, and widget values directly.
- **Environment tools** make `fetch()` calls to backend API endpoints. They query cached scan data about installed nodes, models, and packages.
- **Skills tools** make `fetch()` calls to the skills API endpoints to create/update/delete user skills.
- **Execution tools** interact with ComfyUI's queue API via the frontend to run workflows.

---

## Step-by-step: Adding a new tool

This walkthrough covers all the files you need to touch. We'll use a hypothetical `setNodeTitle` tool as an example.

### 1. Backend definition

Add a new entry to the `TOOLS` list in `tools_definitions.py`:

```python
{
    "type": "function",
    "function": {
        "name": "setNodeTitle",
        "description": "Sets the display title of a node in the workflow.",
        "parameters": {
            "type": "object",
            "properties": {
                "nodeId": {
                    "type": "integer",
                    "description": "The ID of the node to rename"
                },
                "title": {
                    "type": "string",
                    "description": "The new display title for the node"
                }
            },
            "required": ["nodeId", "title"]
        }
    }
}
```

Key rules:
- Use **camelCase** for the tool name
- Match parameter names and types **exactly** with what the frontend will expect
- Write clear descriptions -- the LLM uses these to decide when and how to call the tool

### 2. Frontend Zod schema

Create `ui/src/tools/definitions/set-node-title.ts`:

```typescript
import { z } from 'zod'

export const setNodeTitleDefinition = {
  description: 'Sets the display title of a node in the workflow.',
  parameters: z.object({
    nodeId: z.number(),
    title: z.string()
  })
}
```

The parameter names and types must match the backend definition exactly.

### 3. Frontend implementation

Create `ui/src/tools/implementations/set-node-title.ts`:

```typescript
import type { ToolContext, ToolResult } from '../types'

interface SetNodeTitleParams {
  nodeId: number
  title: string
}

export async function executeSetNodeTitle(
  params: SetNodeTitleParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context
  if (!app?.graph) {
    return { success: false, error: 'ComfyUI app not available' }
  }

  const node = app.graph.getNodeById(params.nodeId)
  if (!node) {
    return { success: false, error: `Node ${params.nodeId} not found` }
  }

  node.title = params.title
  app.graph.setDirtyCanvas(true, true)

  return {
    success: true,
    data: { nodeId: params.nodeId, title: params.title }
  }
}
```

For **graph tools**, use `context.app` (which is `window.app`). For **API tools**, use `fetch()` to call a backend endpoint -- see `refreshEnvironment` or `searchInstalledNodes` implementations for examples.

### 4. Registry registration

Update `ui/src/tools/index.ts`:

```typescript
import { setNodeTitleDefinition } from './definitions/set-node-title'
import { executeSetNodeTitle } from './implementations/set-node-title'

// Inside createTools():
export function createTools(context: ToolContext) {
  return {
    // ... existing tools ...
    setNodeTitle: {
      ...setNodeTitleDefinition,
      execute: (params) => executeSetNodeTitle(params, context)
    }
  }
}
```

### 5. System prompt guidance (if needed)

If the LLM needs instructions on when or how to use the tool, add guidance in `system_context/skills/`. For example, you might update an existing skill file or create a new one.

### 6. Build and test

```bash
cd ui && npm run build
```

Restart ComfyUI (or refresh the browser if the backend didn't change). Test by asking the assistant to use the new tool in conversation.

---

## Step-by-step: Modifying an existing tool

### Changing parameters

If you need to add, remove, or rename a parameter:

1. **Backend**: Update the tool entry in `tools_definitions.py` (change properties, required list, descriptions).
2. **Frontend definition**: Update the Zod schema in `ui/src/tools/definitions/<tool>.ts`.
3. **Frontend implementation**: Update the implementation in `ui/src/tools/implementations/<tool>.ts` to handle the new/changed parameters.
4. **Build**: `cd ui && npm run build`.

Both sides must match. If the backend says a parameter is `required`, the frontend Zod schema should expect it. If you add an optional parameter, use `.optional()` in Zod.

### Renaming a tool

1. Change the `name` in `tools_definitions.py`.
2. Rename (or create new) definition and implementation files.
3. Update the registry key in `ui/src/tools/index.ts`.
4. Update any system prompt guidance that references the old name.
5. Build and test.

---

## Common patterns

### Graph tools

Graph tools work directly with `window.app.graph`:

```typescript
// Pattern: get node, modify it, refresh canvas
const node = context.app.graph.getNodeById(params.nodeId)
if (!node) return { success: false, error: `Node not found` }

// ... modify node ...

context.app.graph.setDirtyCanvas(true, true) // Always refresh after changes
return { success: true, data: { /* result */ } }
```

Always call `setDirtyCanvas(true, true)` after modifying the graph so the canvas re-renders.

### API tools (environment, skills)

API tools call backend endpoints via `fetch()`:

```typescript
// Pattern: fetch from backend, return result
const response = await fetch('/api/environment/nodes?q=' + params.query)
const data = await response.json()
return { success: true, data }
```

See `refreshEnvironment`, `searchInstalledNodes`, or `createSkill` implementations for real examples.

### Execution tools

Execution tools interact with ComfyUI's prompt queue:

```typescript
// Pattern: queue prompt, wait for result
const result = await context.app.queuePrompt()
return { success: true, data: result }
```

---

## Troubleshooting

### Tool not appearing in LLM responses

- Verify the tool is in the `TOOLS` list in `tools_definitions.py`.
- Check that the tool name is spelled correctly (camelCase).
- Ensure the description clearly explains when to use the tool -- the LLM relies on descriptions to decide which tools to call.

### Tool call fails on frontend

- Check the browser console for errors.
- Verify parameter names and types match between backend and frontend.
- Ensure the Zod schema validates the parameters the LLM is sending.
- Check that the tool is registered in `createTools()` in `ui/src/tools/index.ts`.

### Tool result not sent back to LLM

- The result must be a serializable object (JSON-compatible).
- Check that the agentic loop is working: `shouldResubmitAfterToolResult` in `App.tsx` should return `true` when the last message part is a tool invocation.

### Backend and frontend out of sync

If you see unexpected tool behavior, compare:
- Tool name in `tools_definitions.py` vs registry key in `index.ts`
- Parameter names in `tools_definitions.py` vs Zod schema
- Required fields in `tools_definitions.py` vs optional/required in Zod schema

---

## How do I...

**...find example implementations?**
Look at existing tools in `ui/src/tools/implementations/`. `add-node.ts` is a good graph tool example. `searchInstalledNodes` is a good API tool example.

**...add a tool that needs a new backend endpoint?**
Follow the "Adding a new endpoint" section in [backend.md](backend.md), then create the frontend tool that calls that endpoint.

**...test a tool without the LLM?**
You can call tool implementations directly from the browser console for testing, or write unit tests in `ui/src/tools/implementations/__tests__/`.

---

## Related docs

- [Architecture](architecture.md) -- End-to-end tool call flow diagram
- [Backend](backend.md) -- Tool definitions format, API endpoints
- [Frontend](frontend.md) -- Tool registration in the runtime, `window.app` access
- [Standards and conventions](standards-and-conventions.md) -- TypeScript style, Zod validation rules
