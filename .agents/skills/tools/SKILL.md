---
name: tools
description: Agentic tools system for ComfyUI interaction. Use when implementing tools, function calling, or enabling LLM-driven actions in ComfyUI workflows.
version: 0.0.1
license: MIT
---

# Agentic Tools System

**Enable AI assistant to interact with ComfyUI workflows through tools/function calling.**

## References

- [./references/architecture.md](./references/architecture.md) -- System architecture and design patterns
- [./references/implementation.md](./references/implementation.md) -- Step-by-step implementation guide
- [./references/definitions.md](./references/definitions.md) -- Creating tool definitions
- [./references/backend-integration.md](./references/backend-integration.md) -- Backend setup and function calling
- [./references/examples.md](./references/examples.md) -- Tool examples and usage patterns

## Overview

The agentic tools system allows the AI assistant to:
- Add, remove, and modify ComfyUI nodes
- Connect nodes and manage workflows
- Query workflow information
- Execute actions based on user requests

## Architecture

```
Frontend (TypeScript)          Backend (Python)
┌─────────────────────┐       ┌──────────────────┐
│  useLocalRuntime    │       │   Groq API       │
│  ┌───────────────┐  │       │  ┌────────────┐  │
│  │ createTools() │  │       │  │ tools=TOOLS│  │
│  └───────────────┘  │       │  └────────────┘  │
│         ↓           │       │         ↓        │
│  ┌───────────────┐  │       │  ┌────────────┐  │
│  │   Executes    │◄─┼───────┼──│ Declares   │  │
│  │   Actions     │  │       │  │   Tools    │  │
│  └───────────────┘  │       │  └────────────┘  │
│         ↓           │       │                  │
│  ┌───────────────┐  │       │                  │
│  │ window.app    │  │       │                  │
│  │  (ComfyUI)    │  │       │                  │
│  └───────────────┘  │       │                  │
└─────────────────────┘       └──────────────────┘
```

## Quick Start

### 1. Frontend Setup

```typescript
// App.tsx
import { useLocalRuntime } from "@assistant-ui/react";
import { AssistantChatTransport } from "@assistant-ui/react-ai-sdk";
import { createTools } from "@/tools";

function App() {
  const runtime = useLocalRuntime({
    adapter: new AssistantChatTransport({ api: "/api/chat" }),
    tools: window.app ? createTools({ app: window.app }) : {},
  });
  
  return (
    <AssistantRuntimeProvider runtime={runtime}>
      <Thread />
    </AssistantRuntimeProvider>
  );
}
```

### 2. Backend Setup

```python
# __init__.py
from tools_definitions import TOOLS

stream = await client.chat.completions.create(
    model=GROQ_MODEL,
    messages=openai_messages,
    tools=TOOLS,  # Enable function calling
    stream=True,
)
```

## Available Tools

| Tool | Description | Status |
|------|-------------|--------|
| `addNode` | Add node to workflow | ✅ Implemented |
| `removeNode` | Remove node from workflow | ✅ Implemented |
| `connectNodes` | Connect two nodes | ✅ Implemented |
| `getWorkflowInfo` | Get workflow information (with widget data) | ✅ Implemented |
| `setNodeWidgetValue` | Set any widget value on a node | ✅ Implemented |
| `fillPromptNode` | Set prompt text on CLIPTextEncode | ✅ Implemented |
| `refreshEnvironment` | Rescan installed nodes, packages, models | ✅ Implemented |
| `searchInstalledNodes` | Search installed node types | ✅ Implemented |
| `readDocumentation` | Fetch documentation for a topic | ✅ Implemented |
| `createSkill` | Create a persistent user skill | ✅ Implemented |
| `deleteSkill` | Delete a user skill by slug | ✅ Implemented |
| `updateSkill` | Update a user skill by slug (name, description, instructions) | ✅ Implemented |

## Folder Structure

```
ui/src/tools/
├── types.ts              # Shared types
├── index.ts              # Tool registry
├── definitions/          # Zod schemas & metadata
│   ├── add-node.ts
│   ├── remove-node.ts
│   ├── connect-nodes.ts
│   ├── get-workflow-info.ts
│   ├── set-node-widget-value.ts
│   ├── fill-prompt-node.ts
│   ├── create-skill.ts
│   ├── delete-skill.ts
│   ├── update-skill.ts
│   ├── refresh-environment.ts
│   ├── search-installed-nodes.ts
│   └── read-documentation.ts
└── implementations/      # Execution logic
    ├── add-node.ts
    ├── remove-node.ts
    ├── connect-nodes.ts
    ├── get-workflow-info.ts
    ├── set-node-widget-value.ts
    ├── fill-prompt-node.ts
    ├── create-skill.ts
    ├── delete-skill.ts
    ├── update-skill.ts
    ├── refresh-environment.ts
    ├── search-installed-nodes.ts
    └── read-documentation.ts

tools_definitions.py      # Backend tool declarations (single source of truth)
```

## Key Concepts

### Tool Context
All tools receive a `ToolContext` with access to ComfyUI:

```typescript
interface ToolContext {
  app: ComfyApp;
}
```

### Tool Result
Tools return a standardized result:

```typescript
interface ToolResult<T = unknown> {
  success: boolean;
  data?: T;
  error?: string;
}
```

### Execution Flow

1. **User Request** → "Add a KSampler node"
2. **LLM Decision** → Calls `addNode` tool
3. **Frontend Execution** → Creates node in ComfyUI
4. **Result** → Returns node ID and position
5. **LLM Response** → "I've added a KSampler node at position..."

## Adding a New Tool

### 1. Create Definition

```typescript
// tools/definitions/my-tool.ts
import { z } from 'zod';

export const myToolSchema = z.object({
  param: z.string().describe("Parameter description")
});

export const myToolDefinition = {
  name: "myTool",
  description: "What the tool does",
  parameters: myToolSchema,
};
```

### 2. Create Implementation

```typescript
// tools/implementations/my-tool.ts
export async function executeMyTool(
  params: MyToolParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context;
  
  try {
    // Tool logic
    return { success: true, data: { /* result */ } };
  } catch (error) {
    return { 
      success: false, 
      error: error instanceof Error ? error.message : "Unknown error"
    };
  }
}
```

### 3. Register Tool

```typescript
// tools/index.ts
export function createTools(context: ToolContext) {
  return {
    [myToolDefinition.name]: {
      description: myToolDefinition.description,
      parameters: myToolDefinition.parameters,
      execute: async (params) => executeMyTool(params, context)
    }
  };
}
```

### 4. Add to Backend

```python
# tools_definitions.py
TOOLS.append({
    "type": "function",
    "function": {
        "name": "myTool",
        "description": "What the tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param": {"type": "string"}
            }
        }
    }
})
```

## Best Practices

1. **Always validate** `app` and `app.graph` exist
2. **Use try-catch** and return proper `ToolResult`
3. **Update canvas** with `app.graph.setDirtyCanvas(true, true)`
4. **Write clear descriptions** for LLM understanding
5. **Keep tools focused** - one action per tool
6. **Type safety** - leverage TypeScript and Zod

## Troubleshooting

### Tools not executing
- Check `window.app` is available
- Verify `useLocalRuntime` is used (not `useChatRuntime`)
- Ensure tools are registered in runtime

### LLM not using tools
- Add `tools=TOOLS` to backend API call
- Use a model that supports function calling
- Add system message explaining available tools

### Backend integration issues
- Verify tool definitions match frontend
- Check SSE event format for tool calls
- Test with simple tool first (e.g., `getWorkflowInfo`)

## Next Steps

1. Review [architecture.md](./references/architecture.md) for design patterns
2. Follow [implementation.md](./references/implementation.md) for setup
3. Check [examples.md](./references/examples.md) for usage patterns
4. Read [backend-integration.md](./references/backend-integration.md) for streaming setup

## Resources

- **Assistant UI**: https://www.assistant-ui.com/
- **ComfyUI Frontend Types**: https://github.com/Comfy-Org/ComfyUI_frontend
- **Groq Function Calling**: https://console.groq.com/docs/tool-use
- **Zod**: https://zod.dev/
