# Tools - Agentic Tool System

This directory contains all the tools that the AI assistant can use to interact with ComfyUI.

## 📁 Structure

```
tools/
├── types.ts                    # Shared TypeScript types
├── index.ts                    # Central registry of all tools
│
├── definitions/                # Tool definitions (schemas and metadata)
│   ├── index.ts
│   ├── add-node.ts
│   ├── remove-node.ts
│   ├── connect-nodes.ts
│   └── get-workflow-info.ts
│
└── implementations/            # Implementations (execution logic)
    ├── index.ts
    ├── add-node.ts
    ├── remove-node.ts
    ├── connect-nodes.ts
    └── get-workflow-info.ts
```

## 🛠️ Available Tools

### 1. **addNode**
Adds a new node to the ComfyUI workflow.

**Parameters:**
- `nodeType` (string): Node type (e.g., 'KSampler', 'CheckpointLoaderSimple')
- `position` (optional): Object with coordinates `{ x: number, y: number }`

**Example usage by LLM:**
```
"Add a KSampler node at position 200, 300"
```

### 2. **removeNode**
Removes an existing node from the workflow.

**Parameters:**
- `nodeId` (number): ID of the node to remove

**Example usage by LLM:**
```
"Remove node with ID 5"
```

### 3. **connectNodes**
Connects two nodes in the workflow.

**Parameters:**
- `sourceNodeId` (number): ID of the source node
- `sourceSlot` (number): Output slot index
- `targetNodeId` (number): ID of the target node
- `targetSlot` (number): Input slot index

**Example usage by LLM:**
```
"Connect slot 0 of node 3 to slot 1 of node 5"
```

### 4. **getWorkflowInfo**
Gets information about the current workflow.

**Parameters:**
- `includeNodeDetails` (boolean, optional): Whether to include full details of each node

**Example usage by LLM:**
```
"How many nodes are in the workflow?"
"Give me detailed information about the current workflow"
```

## 🚀 Usage

### In the Frontend (App.tsx)

```typescript
import { useLocalRuntime } from "@assistant-ui/react";
import { AssistantChatTransport } from "@assistant-ui/react-ai-sdk";
import { createTools } from "@/tools";

function App() {
  const runtime = useLocalRuntime({
    adapter: new AssistantChatTransport({ api: "/api/chat" }),
    // Register tools with access to window.app
    tools: window.app ? createTools({ app: window.app }) : {}
  });
  
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      {/* ... */}
    </AssistantRuntimeProvider>
  );
}
```

### In the Backend (Python)

The backend needs to declare the same tools so the LLM knows they exist:

```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "addNode",
            "description": "Adds a new node to the ComfyUI workflow",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeType": {"type": "string"},
                    "position": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "number"},
                            "y": {"type": "number"}
                        }
                    }
                }
            }
        }
    },
    # ... more tools
]
```

## ➕ Adding a New Tool

### 1. Create the definition

```typescript
// tools/definitions/my-new-tool.ts
import { z } from 'zod';

export const myNewToolSchema = z.object({
  parameter1: z.string().describe("Parameter description"),
  parameter2: z.number().optional()
});

export const myNewToolDefinition = {
  name: "myNewTool",
  description: "Description of what the tool does",
  parameters: myNewToolSchema,
};

export type MyNewToolParams = z.infer<typeof myNewToolSchema>;
```

### 2. Create the implementation

```typescript
// tools/implementations/my-new-tool.ts
import type { ToolContext, ToolResult } from '../types';
import type { MyNewToolParams } from '../definitions/my-new-tool';

export async function executeMyNewTool(
  params: MyNewToolParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context;
  
  try {
    // Tool logic
    
    return {
      success: true,
      data: { /* result */ }
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error"
    };
  }
}
```

### 3. Export in index.ts files

```typescript
// tools/definitions/index.ts
export * from './my-new-tool';

// tools/implementations/index.ts
export * from './my-new-tool';
```

### 4. Register in tools/index.ts

```typescript
import { myNewToolDefinition } from './definitions';
import { executeMyNewTool } from './implementations';

export function createTools(context: ToolContext): Record<string, Tool> {
  return {
    // ... existing tools
    [myNewToolDefinition.name]: {
      description: myNewToolDefinition.description,
      parameters: myNewToolDefinition.parameters,
      execute: async (params) => executeMyNewTool(params, context)
    }
  };
}
```

### 5. Add to backend (Python)

Add the tool definition to the `tools` array in `__init__.py`.

## 📝 Best Practices

1. **Validation**: Always validate that `app` and `app.graph` exist before using them
2. **Error handling**: Use try-catch and return `ToolResult` with `success: false` on error
3. **Update canvas**: Call `app.graph.setDirtyCanvas(true, true)` after modifying the graph
4. **Clear descriptions**: Write detailed descriptions so the LLM understands when to use each tool
5. **Type safety**: Leverage TypeScript and Zod for type validation

## 🧪 Testing

To test a tool:

```typescript
import { executeMyNewTool } from './implementations/my-new-tool';

const mockApp = {
  graph: {
    // Mock ComfyUI API
  }
};

const result = await executeMyNewTool(
  { parameter1: "test" },
  { app: mockApp as any }
);

expect(result.success).toBe(true);
```

## 🔗 References

- [assistant-ui Documentation](https://www.assistant-ui.com/)
- [ComfyUI Frontend Types](https://github.com/Comfy-Org/ComfyUI_frontend)
- [Zod Documentation](https://zod.dev/)
