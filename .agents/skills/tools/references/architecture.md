# Tools System Architecture

## Overview

The agentic tools system follows a **frontend-execution** pattern where:
- **Backend (LLM)** declares tools and decides when to use them
- **Frontend** executes the actual actions on ComfyUI
- **Results** flow back to the LLM to continue conversation

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         USER                                 │
│                    "Add a KSampler"                         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    FRONTEND (React)                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              AssistantRuntimeProvider                 │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │           useLocalRuntime                       │  │  │
│  │  │  ┌──────────────────────────────────────────┐  │  │  │
│  │  │  │  adapter: AssistantChatTransport         │  │  │  │
│  │  │  │           (sends to /api/chat)           │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  │  ┌──────────────────────────────────────────┐  │  │  │
│  │  │  │  tools: createTools({ app })             │  │  │  │
│  │  │  │    - addNode()                           │  │  │  │
│  │  │  │    - removeNode()                        │  │  │  │
│  │  │  │    - connectNodes()                      │  │  │  │
│  │  │  │    - getWorkflowInfo()                   │  │  │  │
│  │  │  └──────────────────────────────────────────┘  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP POST /api/chat
                           │ (messages + tool results)
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   BACKEND (Python/OpenAI-compatible provider)                     │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         chat_api_handler(request)                     │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  client.chat.completions.create(              │  │  │
│  │  │    model=OPENAI_MODEL,                          │  │  │
│  │  │    messages=openai_messages,                  │  │  │
│  │  │    tools=TOOLS,  ← Tool declarations          │  │  │
│  │  │    stream=True                                │  │  │
│  │  │  )                                            │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                     ↓                                 │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │  Stream SSE Events:                           │  │  │
│  │  │    - text-delta (text content)                │  │  │
│  │  │    - tool-call-delta (tool invocations)       │  │  │
│  │  │    - reasoning-delta (thinking)               │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ SSE Stream
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                   FRONTEND (Execution)                      │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Tool Call Received: addNode({ nodeType: "KSampler" })│  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  executeAddNode(params, { app: window.app })         │  │
│  │    const node = app.graph.add("KSampler")            │  │
│  │    return { success: true, nodeId: node.id }         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           ↓                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │         ComfyUI Graph Updated                         │  │
│  │    (node appears in workflow)                         │  │
│  └──────────────────────────────────────────────────────┘  │
└──────────────────────────┬──────────────────────────────────┘
                           │ Result sent back
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      BACKEND (LLM)                          │
│  Receives: { success: true, nodeId: 42 }                   │
│  Generates: "I've added a KSampler node (ID: 42)..."       │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Tool Context (`ToolContext`)

Provides access to ComfyUI API:

```typescript
interface ToolContext {
  app: ComfyApp;
}
```

**Why?** Dependency injection allows testing without real ComfyUI instance.

### 2. Tool Definition (`definitions/`)

Declares tool metadata and validation schema:

```typescript
export const addNodeDefinition = {
  name: "addNode",
  description: "Adds a new node to the ComfyUI workflow...",
  parameters: z.object({
    nodeType: z.string().describe("Node type..."),
    position: z.object({ x: z.number(), y: z.number() }).optional()
  }),
};
```

**Why separate?** Definitions can be shared between frontend and backend.

### 3. Tool Implementation (`implementations/`)

Executes the actual action:

```typescript
export async function executeAddNode(
  params: AddNodeParams,
  context: ToolContext
): Promise<ToolResult<AddNodeResult>> {
  const { app } = context;
  
  if (!app?.graph) {
    return { success: false, error: "ComfyUI app is not available" };
  }

  const node = app.graph.add(params.nodeType);
  if (!node) {
    return { success: false, error: `Could not create node...` };
  }

  if (params.position) {
    node.pos = [params.position.x, params.position.y];
  }

  app.graph.setDirtyCanvas(true, true);

  return {
    success: true,
    data: { nodeId: node.id, nodeType: params.nodeType, position: node.pos }
  };
}
```

**Why separate?** Clean separation of concerns, easier testing.

### 4. Tool Registry (`index.ts`)

Combines definitions + implementations:

```typescript
export function createTools(context: ToolContext): Record<string, Tool> {
  return {
    [addNodeDefinition.name]: {
      description: addNodeDefinition.description,
      parameters: addNodeDefinition.parameters,
      execute: async (params) => executeAddNode(params, context)
    },
    // ... more tools
  };
}
```

**Why factory function?** Context is injected at runtime when `window.app` is available.

### 5. Backend Declarations (`tools_definitions.py`)

Mirrors frontend tool definitions for the LLM:

```python
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "addNode",
            "description": "Adds a new node to the ComfyUI workflow...",
            "parameters": {
                "type": "object",
                "properties": {
                    "nodeType": {"type": "string", ...},
                    "position": {...}
                }
            }
        }
    }
]
```

**Critical:** Definitions must match exactly between frontend and backend.

## Data Flow

### Request Flow (User → LLM)

1. User sends message: "Add a KSampler"
2. Frontend sends to `/api/chat` via `AssistantChatTransport`
3. Backend receives request with conversation history
4. LLM processes with tool declarations (`tools=TOOLS`)
5. LLM decides to call `addNode` tool

### Tool Call Flow (LLM → Frontend → ComfyUI)

1. LLM generates tool call in response stream
2. Backend streams SSE event: `tool-call-delta`
3. Frontend's `useLocalRuntime` intercepts tool call
4. Frontend executes: `executeAddNode(params, { app })`
5. ComfyUI graph is modified via `window.app.graph.add()`
6. Result returned: `{ success: true, nodeId: 42 }`

### Response Flow (Frontend → LLM → User)

1. Tool result sent back to backend in next request
2. LLM receives result and continues generation
3. LLM generates natural language response
4. Frontend displays: "I've added a KSampler node..."

## Design Patterns

### 1. Dependency Injection

```typescript
// Bad: Direct access
function executeAddNode(params) {
  const node = window.app.graph.add(params.nodeType);
}

// Good: Context injection
function executeAddNode(params, context: ToolContext) {
  const node = context.app.graph.add(params.nodeType);
}
```

**Benefits:**
- Testable (mock `context.app`)
- Flexible (works with different graph implementations)
- Clear dependencies

### 2. Result Objects

```typescript
// Bad: Throw errors
function executeTool(params) {
  if (!app) throw new Error("App not available");
  return data;
}

// Good: Return result object
function executeTool(params): ToolResult {
  if (!app) return { success: false, error: "App not available" };
  return { success: true, data };
}
```

**Benefits:**
- No try-catch needed at call site
- Consistent error handling
- Type-safe results

### 3. Schema-Driven Validation

```typescript
// Definition provides runtime validation
export const addNodeSchema = z.object({
  nodeType: z.string(),
  position: z.object({ x: z.number(), y: z.number() }).optional()
});

// Implementation gets type-safe params
function executeAddNode(
  params: z.infer<typeof addNodeSchema>,
  context: ToolContext
) { ... }
```

**Benefits:**
- Runtime validation via Zod
- TypeScript type inference
- Self-documenting code

### 4. Separation of Concerns

```
definitions/     → What the tool does (metadata)
implementations/ → How the tool works (logic)
index.ts         → Wire them together
```

**Benefits:**
- Single responsibility
- Easy to add new tools
- Reusable definitions

## Why Frontend Execution?

### Alternative: Backend Execution

```
User → Backend (LLM) → Backend executes → ComfyUI API
```

**Problems:**
- Need to expose ComfyUI API to network
- CORS, security, authentication issues
- Latency (extra network hop)
- Can't access `window.app` directly

### Our Approach: Frontend Execution

```
User → Backend (LLM) → Frontend executes → window.app
```

**Advantages:**
- Direct access to `window.app` (ComfyUI)
- No network exposure needed
- Faster execution
- Standard pattern for AI SDK
- Security: no backend → ComfyUI connection needed

## Tool Lifecycle

```
1. DEFINITION
   └─ Create schema with Zod
   └─ Add description for LLM

2. IMPLEMENTATION
   └─ Write execution logic
   └─ Handle errors gracefully
   └─ Return ToolResult

3. REGISTRATION
   └─ Add to createTools()
   └─ Export from index.ts

4. BACKEND DECLARATION
   └─ Add to tools_definitions.py
   └─ Match schema exactly

5. RUNTIME
   └─ LLM sees tool in context
   └─ LLM calls tool when appropriate
   └─ Frontend executes action
   └─ Result flows back to LLM
```

## Performance Considerations

### Tool Execution Speed
- Tools execute synchronously in browser
- Direct access to `window.app` (no IPC)
- Typical execution: < 10ms

### Network Overhead
- Tool declaration: one-time in context
- Tool call: lightweight JSON in SSE stream
- Tool result: included in next request

### Scalability
- Number of tools limited by context window
- Each tool adds ~100-500 tokens to context
- Recommend: 5-15 tools per agent

## Security Considerations

1. **Validation**: All params validated with Zod before execution
2. **Error handling**: Failures don't crash the app
3. **Permissions**: Tools only have access to what user can do
4. **Sandboxing**: Tools can't access filesystem/network directly

## Next Steps

- Read [implementation.md](./implementation.md) for setup guide
- See [definitions.md](./definitions.md) for creating tools
- Check [backend-integration.md](./backend-integration.md) for streaming
- Review [examples.md](./examples.md) for patterns
