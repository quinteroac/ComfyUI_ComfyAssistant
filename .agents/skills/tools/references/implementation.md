# Implementation Guide

Complete step-by-step guide to implement the agentic tools system.

## Prerequisites

- ComfyUI project with React frontend
- `@assistant-ui/react` installed
- Backend with streaming support (Groq/OpenAI)
- TypeScript configured

## Step 1: Create Tool Structure

### Create base directories

```bash
cd ui/src
mkdir -p tools/definitions tools/implementations
```

### Create types file

```typescript
// ui/src/tools/types.ts
import type { ComfyApp } from '@comfyorg/comfyui-frontend-types';
import { z } from 'zod';

export interface ToolContext {
  app: ComfyApp;
}

export interface ToolDefinition<TParams extends z.ZodSchema> {
  name: string;
  description: string;
  parameters: TParams;
  execute: (params: z.infer<TParams>, context: ToolContext) => Promise<unknown>;
}

export interface ToolResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}
```

## Step 2: Create Your First Tool

### Define the tool schema

```typescript
// ui/src/tools/definitions/add-node.ts
import { z } from 'zod';

export const addNodeSchema = z.object({
  nodeType: z.string().describe("Node type to add"),
  position: z.object({
    x: z.number(),
    y: z.number()
  }).optional().describe("Optional position")
});

export const addNodeDefinition = {
  name: "addNode",
  description: "Adds a new node to the ComfyUI workflow",
  parameters: addNodeSchema,
};

export type AddNodeParams = z.infer<typeof addNodeSchema>;
```

### Implement the tool logic

```typescript
// ui/src/tools/implementations/add-node.ts
import type { ToolContext, ToolResult } from '../types';
import type { AddNodeParams } from '../definitions/add-node';

interface AddNodeResult {
  nodeId: number;
  nodeType: string;
  position: [number, number];
}

export async function executeAddNode(
  params: AddNodeParams,
  context: ToolContext
): Promise<ToolResult<AddNodeResult>> {
  const { app } = context;
  
  // Validate app availability
  if (!app?.graph) {
    return {
      success: false,
      error: "ComfyUI app is not available"
    };
  }

  try {
    // Execute the action
    const node = app.graph.add(params.nodeType);
    
    if (!node) {
      return {
        success: false,
        error: `Could not create node of type: ${params.nodeType}`
      };
    }

    // Apply optional parameters
    if (params.position) {
      node.pos = [params.position.x, params.position.y];
    }

    // Update the canvas
    app.graph.setDirtyCanvas(true, true);

    // Return success result
    return {
      success: true,
      data: {
        nodeId: node.id,
        nodeType: params.nodeType,
        position: node.pos as [number, number]
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    };
  }
}
```

### Create barrel exports

```typescript
// ui/src/tools/definitions/index.ts
export * from './add-node';

// ui/src/tools/implementations/index.ts
export * from './add-node';
```

## Step 3: Create Tool Registry

```typescript
// ui/src/tools/index.ts
import type { ToolContext } from './types';
import type { Tool } from '@assistant-ui/react';

import { addNodeDefinition } from './definitions';
import { executeAddNode } from './implementations';

export function createTools(context: ToolContext): Record<string, Tool> {
  return {
    [addNodeDefinition.name]: {
      description: addNodeDefinition.description,
      parameters: addNodeDefinition.parameters,
      execute: async (params) => executeAddNode(params, context)
    }
  };
}

export * from './definitions';
export * from './types';
```

## Step 4: Update Frontend Runtime

### Modify App.tsx

```typescript
// ui/src/App.tsx
import { ComfyApp } from '@comfyorg/comfyui-frontend-types';
import { AssistantRuntimeProvider, useLocalRuntime } from "@assistant-ui/react";
import { AssistantChatTransport } from "@assistant-ui/react-ai-sdk";
import { createTools } from "@/tools";

declare global {
  interface Window {
    app?: ComfyApp;
  }
}

function App() {
  // Change from useChatRuntime to useLocalRuntime
  const runtime = useLocalRuntime({
    adapter: new AssistantChatTransport({ api: "/api/chat" }),
    
    // Register tools
    tools: window.app ? createTools({ app: window.app }) : {},
  });
  
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {/* Your UI components */}
    </AssistantRuntimeProvider>
  );
}

export default App;
```

**Key changes:**
1. Import `useLocalRuntime` instead of `useChatRuntime`
2. Use `adapter` prop instead of `transport`
3. Add `tools` prop with `createTools()`

## Step 5: Backend Integration

### Create tool definitions

```python
# tools_definitions.py
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "addNode",
            "description": "Adds a new node to the ComfyUI workflow",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeType": {
                        "type": "string",
                        "description": "Node type to add"
                    },
                    "position": {
                        "type": "object",
                        "description": "Optional position",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}
                        }
                    }
                },
                "required": ["nodeType"]
            }
        }
    }
]

def get_tools():
    return TOOLS
```

### Update backend handler

```python
# __init__.py
from tools_definitions import TOOLS

async def chat_api_handler(request: web.Request) -> web.Response:
    # ... existing code ...
    
    # Add tools to API call
    stream = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=openai_messages,
        tools=TOOLS,  # ← Enable function calling
        stream=True,
    )
    
    # Stream handling remains the same
    # The AI SDK in frontend handles tool execution
```

## Step 6: Build and Test

### Rebuild frontend

```bash
cd ui
npm run build
```

### Restart ComfyUI

Restart ComfyUI to load the new backend code.

### Test basic functionality

1. Open ComfyUI
2. Open browser console (F12)
3. Verify `window.app` exists:
```javascript
console.log(window.app);
```

### Test tool execution

Open the chat and try:
```
"Add a KSampler node at position 100, 200"
```

Expected behavior:
1. Assistant thinks about the request
2. Calls `addNode` tool
3. Node appears in the workflow
4. Assistant confirms: "I've added a KSampler node..."

## Step 7: Add More Tools

Follow the same pattern for additional tools:

### removeNode tool

```typescript
// definitions/remove-node.ts
export const removeNodeSchema = z.object({
  nodeId: z.number()
});

// implementations/remove-node.ts
export async function executeRemoveNode(params, context) {
  const node = context.app.graph.getNodeById(params.nodeId);
  if (!node) {
    return { success: false, error: "Node not found" };
  }
  context.app.graph.remove(node);
  context.app.graph.setDirtyCanvas(true, true);
  return { success: true, data: { removed: true } };
}
```

### Register in createTools()

```typescript
export function createTools(context: ToolContext) {
  return {
    addNode: { /* ... */ },
    removeNode: {
      description: removeNodeDefinition.description,
      parameters: removeNodeDefinition.parameters,
      execute: async (params) => executeRemoveNode(params, context)
    }
  };
}
```

### Add to backend

```python
TOOLS.append({
    "type": "function",
    "function": {
        "name": "removeNode",
        "description": "Removes a node from the workflow",
        "parameters": {
            "type": "object",
            "properties": {
                "nodeId": {"type": "number"}
            },
            "required": ["nodeId"]
        }
    }
})
```

## Common Patterns

### Pattern 1: Query Tool (Read-only)

```typescript
export async function executeGetWorkflowInfo(
  params: GetWorkflowInfoParams,
  context: ToolContext
): Promise<ToolResult<WorkflowInfo>> {
  const { app } = context;
  
  const nodes = app.graph._nodes.map(node => ({
    id: node.id,
    type: node.type,
    position: node.pos
  }));
  
  return {
    success: true,
    data: { nodeCount: nodes.length, nodes }
  };
}
```

### Pattern 2: Mutation Tool (Write)

```typescript
export async function executeConnectNodes(
  params: ConnectNodesParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context;
  
  const sourceNode = app.graph.getNodeById(params.sourceNodeId);
  const targetNode = app.graph.getNodeById(params.targetNodeId);
  
  if (!sourceNode || !targetNode) {
    return { success: false, error: "Nodes not found" };
  }
  
  const linkId = sourceNode.connect(
    params.sourceSlot, 
    targetNode, 
    params.targetSlot
  );
  
  app.graph.setDirtyCanvas(true, true);
  
  return { success: true, data: { linkId } };
}
```

### Pattern 3: Validation-Heavy Tool

```typescript
export async function executeSetNodeWidget(
  params: SetNodeWidgetParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context;
  
  // Find node
  const node = app.graph.getNodeById(params.nodeId);
  if (!node) {
    return { success: false, error: "Node not found" };
  }
  
  // Validate widget exists
  const widget = node.widgets?.find(w => w.name === params.widgetName);
  if (!widget) {
    return { 
      success: false, 
      error: `Widget '${params.widgetName}' not found on node` 
    };
  }
  
  // Validate value type
  if (typeof params.value !== typeof widget.value) {
    return { 
      success: false, 
      error: `Invalid type for widget '${params.widgetName}'` 
    };
  }
  
  // Set value
  widget.value = params.value;
  app.graph.setDirtyCanvas(true, true);
  
  return { success: true, data: { updated: true } };
}
```

## Troubleshooting

### Issue: "window.app is undefined"

**Cause:** ComfyUI not fully loaded when tools are registered.

**Solution:** Tools are created conditionally:
```typescript
tools: window.app ? createTools({ app: window.app }) : {}
```

### Issue: Tools not executing

**Checklist:**
- [ ] Using `useLocalRuntime` (not `useChatRuntime`)
- [ ] Tools registered in runtime
- [ ] `window.app` exists
- [ ] No console errors

### Issue: LLM not using tools

**Checklist:**
- [ ] `tools=TOOLS` in backend call
- [ ] Model supports function calling
- [ ] Tool descriptions are clear
- [ ] Tool names match exactly

### Issue: Type errors

**Fix:** Ensure Zod schema matches TypeScript types:
```typescript
export const schema = z.object({ ... });
export type Params = z.infer<typeof schema>;
```

## Best Practices

1. **Always validate inputs**
   ```typescript
   if (!app?.graph) {
     return { success: false, error: "App not available" };
   }
   ```

2. **Update canvas after mutations**
   ```typescript
   app.graph.setDirtyCanvas(true, true);
   ```

3. **Return descriptive errors**
   ```typescript
   return { 
     success: false, 
     error: `Node with ID ${id} not found` 
   };
   ```

4. **Use TypeScript types**
   ```typescript
   export type Params = z.infer<typeof schema>;
   ```

5. **Write clear descriptions**
   ```typescript
   description: "Adds a new node to the ComfyUI workflow. Allows specifying the node type and optionally its position on the canvas."
   ```

## Next Steps

- Review [definitions.md](./definitions.md) for schema best practices
- Check [backend-integration.md](./backend-integration.md) for streaming
- See [examples.md](./examples.md) for more patterns
