---
name: backend-tools-declaration
description: How tools are declared on backend and frontend, and how to keep them in sync
version: 0.0.1
license: MIT
---

# Backend Tools Declaration

Tools are declared in two places that must stay in sync: the Python backend (for the LLM) and the TypeScript frontend (for execution).

## Backend: `tools_definitions.py`

Tools are declared in OpenAI function calling format as a `TOOLS` list:

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "addNode",
            "description": "Adds a node to the workflow...",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeType": {"type": "string", "description": "..."},
                    "position": {
                        "type": "object",
                        "properties": {"x": {"type": "number"}, "y": {"type": "number"}}
                    }
                },
                "required": ["nodeType"]
            }
        }
    },
    ...
]
```

Helper functions: `get_tools()` returns the list, `get_tool_names()` returns name strings.

## Frontend: Zod Schemas + Implementations

**Definitions** (`ui/src/tools/definitions/`): Each tool has a Zod schema file.

```typescript
// add-node.ts
export const addNodeDefinition = {
  description: 'Adds a node to the workflow...',
  parameters: z.object({
    nodeType: z.string(),
    position: z.object({ x: z.number(), y: z.number() }).optional()
  })
}
```

**Implementations** (`ui/src/tools/implementations/`): Each tool has an execute function.

```typescript
// add-node.ts
export async function executeAddNode(
  params: AddNodeParams,
  context: ToolContext
): Promise<ToolResult> { ... }
```

**Registry** (`ui/src/tools/index.ts`): `createTools(context)` combines definitions and implementations into a `Record<string, Tool>` consumed by the runtime.

**Hook** (`ui/src/tools/useComfyTools.ts`): `useComfyTools()` calls `createTools()` and registers them into the `ModelContext` via `useAssistantTool()` or similar.

## Current Tools

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

**Graph tools** execute in the frontend against `window.app`. **Environment/Skills tools** call backend API endpoints. **Execution tools** interact with ComfyUI's queue API via the frontend.

## Sync Checklist: Adding a New Tool

1. **Backend** -- Add entry to `TOOLS` list in `tools_definitions.py`:
   - Use OpenAI function calling format
   - Match the tool name exactly (camelCase)
   - Document all parameters with descriptions

2. **Frontend definition** -- Create `ui/src/tools/definitions/<tool-name>.ts`:
   - Export a definition object with `description` and `parameters` (Zod schema)
   - Parameter names and types must match the backend exactly

3. **Frontend implementation** -- Create `ui/src/tools/implementations/<tool-name>.ts`:
   - Export an `execute<ToolName>` function
   - Signature: `(params, context) => Promise<ToolResult>`

4. **Registry** -- Update `ui/src/tools/index.ts`:
   - Import the definition and implementation
   - Add to the object returned by `createTools()`

5. **System prompt** (if needed) -- Update `system_context/skills/` with usage guidance for the LLM

6. **Rebuild** -- `cd ui && npm run build`

7. **Test** -- Verify the LLM can call the tool and the frontend executes it correctly

## FAQ

### I added a tool in TypeScript -- what must I change in Python?
Add a matching entry to `TOOLS` in `tools_definitions.py` with the same name, parameter names, types, and descriptions. The LLM only sees the backend definitions.

### Where do I change a tool's name, description, or parameters?
Both places: `tools_definitions.py` (backend) and `ui/src/tools/definitions/<tool>.ts` (frontend). They must match.

### How do I add a tool that calls a backend API instead of `window.app`?
Same process, but the frontend implementation makes a `fetch()` call to a backend endpoint instead of using `window.app`. See `refreshEnvironment` or `searchInstalledNodes` implementations for examples.

### How are tool results returned to the LLM?
The frontend executes the tool, wraps the result as a tool-result message part, and the runtime resubmits the full message history (including the result) to POST `/api/chat`. The backend converts it to an OpenAI `tool` role message.

## Related Skills

- `backend-architecture` -- backend module map and API endpoints
- `architecture-overview` -- end-to-end tool call flow diagram
