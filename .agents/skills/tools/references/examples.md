# Tool Examples and Patterns

Real-world examples of tool implementations and usage patterns.

## Complete Tool Examples

### Example 1: Add Node Tool

**Definition:**
```typescript
// tools/definitions/add-node.ts
import { z } from 'zod';

export const addNodeSchema = z.object({
  nodeType: z.string().describe(
    "Node type to add (e.g., 'KSampler', 'CheckpointLoaderSimple', 'LoadImage')"
  ),
  position: z.object({
    x: z.number().describe("X coordinate on canvas"),
    y: z.number().describe("Y coordinate on canvas")
  }).optional().describe("Optional position. Defaults to (0, 0) if not specified"),
  title: z.string().optional().describe("Custom title for the node")
});

export const addNodeDefinition = {
  name: "addNode",
  description: "Adds a new node to the ComfyUI workflow. Use this when the user wants to add nodes like KSampler, LoadImage, SaveImage, etc.",
  parameters: addNodeSchema,
};

export type AddNodeParams = z.infer<typeof addNodeSchema>;
```

**Implementation:**
```typescript
// tools/implementations/add-node.ts
import type { ToolContext, ToolResult } from '../types';
import type { AddNodeParams } from '../definitions/add-node';

interface AddNodeResult {
  nodeId: number;
  nodeType: string;
  position: [number, number];
  title: string;
}

export async function executeAddNode(
  params: AddNodeParams,
  context: ToolContext
): Promise<ToolResult<AddNodeResult>> {
  const { app } = context;
  
  if (!app?.graph) {
    return {
      success: false,
      error: "ComfyUI app is not available"
    };
  }

  try {
    // Add node to graph
    const node = app.graph.add(params.nodeType);
    
    if (!node) {
      return {
        success: false,
        error: `Could not create node of type: ${params.nodeType}. Check that this node type exists.`
      };
    }

    // Set position if provided
    if (params.position) {
      node.pos = [params.position.x, params.position.y];
    }

    // Set custom title if provided
    if (params.title) {
      node.title = params.title;
    }

    // Mark canvas as dirty to trigger redraw
    app.graph.setDirtyCanvas(true, true);

    return {
      success: true,
      data: {
        nodeId: node.id,
        nodeType: params.nodeType,
        position: node.pos as [number, number],
        title: node.title || params.nodeType
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error adding node"
    };
  }
}
```

**Usage Examples:**
```
User: "Add a KSampler node"
→ Tool call: addNode({ nodeType: "KSampler" })
→ Result: { success: true, data: { nodeId: 1, nodeType: "KSampler", position: [0, 0], title: "KSampler" } }

User: "Add a LoadImage node at position 100, 200"
→ Tool call: addNode({ nodeType: "LoadImage", position: { x: 100, y: 200 } })

User: "Add a checkpoint loader called 'My Model' at 50, 50"
→ Tool call: addNode({ nodeType: "CheckpointLoaderSimple", position: { x: 50, y: 50 }, title: "My Model" })
```

### Example 2: Get Workflow Info Tool

**Definition:**
```typescript
// tools/definitions/get-workflow-info.ts
import { z } from 'zod';

export const getWorkflowInfoSchema = z.object({
  includeNodeDetails: z.boolean()
    .optional()
    .default(false)
    .describe("Include detailed node information (widgets, connections, etc.)"),
  filterByType: z.string()
    .optional()
    .describe("Filter nodes by type (e.g., 'KSampler')")
});

export const getWorkflowInfoDefinition = {
  name: "getWorkflowInfo",
  description: "Gets information about the current workflow including node count, types, positions, and connections. Use this to answer questions about the workflow state.",
  parameters: getWorkflowInfoSchema,
};

export type GetWorkflowInfoParams = z.infer<typeof getWorkflowInfoSchema>;
```

**Implementation:**
```typescript
// tools/implementations/get-workflow-info.ts
import type { ToolContext, ToolResult } from '../types';
import type { GetWorkflowInfoParams } from '../definitions/get-workflow-info';

interface NodeInfo {
  id: number;
  type: string;
  position: [number, number];
  title?: string;
  size?: [number, number];
  widgets?: Array<{ name: string; value: any }>;
}

interface ConnectionInfo {
  sourceNodeId: number;
  sourceSlot: number;
  targetNodeId: number;
  targetSlot: number;
}

interface WorkflowInfo {
  nodeCount: number;
  nodes: NodeInfo[];
  connections: ConnectionInfo[];
  nodeTypes: Record<string, number>;
}

export async function executeGetWorkflowInfo(
  params: GetWorkflowInfoParams,
  context: ToolContext
): Promise<ToolResult<WorkflowInfo>> {
  const { app } = context;
  
  if (!app?.graph) {
    return {
      success: false,
      error: "ComfyUI app is not available"
    };
  }

  try {
    const nodes: NodeInfo[] = [];
    const connections: ConnectionInfo[] = [];
    const nodeTypes: Record<string, number> = {};

    // Iterate through all nodes
    for (const node of app.graph._nodes) {
      // Apply filter if specified
      if (params.filterByType && node.type !== params.filterByType) {
        continue;
      }

      // Count node types
      nodeTypes[node.type] = (nodeTypes[node.type] || 0) + 1;

      // Build node info
      const nodeInfo: NodeInfo = {
        id: node.id,
        type: node.type,
        position: node.pos as [number, number],
      };

      if (params.includeNodeDetails) {
        nodeInfo.title = node.title;
        nodeInfo.size = node.size as [number, number];
        
        // Include widget values
        if (node.widgets) {
          nodeInfo.widgets = node.widgets.map(w => ({
            name: w.name,
            value: w.value
          }));
        }
      }

      nodes.push(nodeInfo);

      // Collect connections
      if (node.outputs) {
        for (let i = 0; i < node.outputs.length; i++) {
          const output = node.outputs[i];
          if (output.links) {
            for (const linkId of output.links) {
              const link = app.graph.links[linkId];
              if (link) {
                connections.push({
                  sourceNodeId: node.id,
                  sourceSlot: i,
                  targetNodeId: link.target_id,
                  targetSlot: link.target_slot
                });
              }
            }
          }
        }
      }
    }

    return {
      success: true,
      data: {
        nodeCount: nodes.length,
        nodes,
        connections,
        nodeTypes
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error getting workflow info"
    };
  }
}
```

**Usage Examples:**
```
User: "How many nodes are in my workflow?"
→ Tool call: getWorkflowInfo({})
→ Response: "You have 5 nodes in your workflow"

User: "What types of nodes do I have?"
→ Tool call: getWorkflowInfo({})
→ Response: "You have: 2 KSampler nodes, 1 CheckpointLoader, 1 LoadImage, and 1 SaveImage"

User: "Show me details of all KSampler nodes"
→ Tool call: getWorkflowInfo({ includeNodeDetails: true, filterByType: "KSampler" })
```

### Example 3: Connect Nodes Tool

**Complete Implementation:**
```typescript
// tools/definitions/connect-nodes.ts
import { z } from 'zod';

export const connectNodesSchema = z.object({
  sourceNodeId: z.number().describe("ID of the source node"),
  sourceSlot: z.number().int().min(0).describe("Output slot index (0-based)"),
  targetNodeId: z.number().describe("ID of the target node"),
  targetSlot: z.number().int().min(0).describe("Input slot index (0-based)")
});

export const connectNodesDefinition = {
  name: "connectNodes",
  description: "Connects two nodes by creating a link from an output slot of the source node to an input slot of the target node.",
  parameters: connectNodesSchema,
};

// tools/implementations/connect-nodes.ts
export async function executeConnectNodes(
  params: ConnectNodesParams,
  context: ToolContext
): Promise<ToolResult<ConnectNodesResult>> {
  const { app } = context;
  
  if (!app?.graph) {
    return { success: false, error: "ComfyUI app is not available" };
  }

  try {
    const sourceNode = app.graph.getNodeById(params.sourceNodeId);
    const targetNode = app.graph.getNodeById(params.targetNodeId);
    
    if (!sourceNode) {
      return { 
        success: false, 
        error: `Source node ${params.sourceNodeId} not found` 
      };
    }
    
    if (!targetNode) {
      return { 
        success: false, 
        error: `Target node ${params.targetNodeId} not found` 
      };
    }

    // Validate slots
    if (!sourceNode.outputs || params.sourceSlot >= sourceNode.outputs.length) {
      return {
        success: false,
        error: `Source node has no output at slot ${params.sourceSlot}`
      };
    }

    if (!targetNode.inputs || params.targetSlot >= targetNode.inputs.length) {
      return {
        success: false,
        error: `Target node has no input at slot ${params.targetSlot}`
      };
    }

    // Create connection
    const linkId = sourceNode.connect(
      params.sourceSlot,
      targetNode,
      params.targetSlot
    );
    
    if (linkId === null || linkId === undefined) {
      return {
        success: false,
        error: "Failed to create connection. Data types may be incompatible."
      };
    }

    app.graph.setDirtyCanvas(true, true);

    return {
      success: true,
      data: {
        linkId,
        sourceNodeId: params.sourceNodeId,
        sourceSlot: params.sourceSlot,
        targetNodeId: params.targetNodeId,
        targetSlot: params.targetSlot
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

## Advanced Patterns

### Pattern 1: Tool with Validation

```typescript
export async function executeSetNodeWidget(
  params: SetNodeWidgetParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context;
  
  if (!app?.graph) {
    return { success: false, error: "App not available" };
  }

  try {
    // Find node
    const node = app.graph.getNodeById(params.nodeId);
    if (!node) {
      return { success: false, error: `Node ${params.nodeId} not found` };
    }

    // Find widget
    const widget = node.widgets?.find(w => w.name === params.widgetName);
    if (!widget) {
      return { 
        success: false, 
        error: `Widget '${params.widgetName}' not found. Available: ${node.widgets?.map(w => w.name).join(', ')}` 
      };
    }

    // Validate type
    const valueType = typeof params.value;
    const widgetType = typeof widget.value;
    
    if (valueType !== widgetType) {
      return {
        success: false,
        error: `Type mismatch: expected ${widgetType}, got ${valueType}`
      };
    }

    // Set value
    widget.value = params.value;
    app.graph.setDirtyCanvas(true, true);

    return { success: true, data: { nodeId: params.nodeId, widgetName: params.widgetName, value: params.value } };
  } catch (error) {
    return { success: false, error: String(error) };
  }
}
```

### Pattern 2: Tool with Complex Logic

```typescript
export async function executeCreateKSamplerWorkflow(
  params: CreateKSamplerWorkflowParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context;
  
  if (!app?.graph) {
    return { success: false, error: "App not available" };
  }

  try {
    const createdNodes: number[] = [];
    let lastNode: any = null;
    let lastSlot = 0;

    // Helper to add and position nodes
    const addNode = (type: string, x: number, y: number) => {
      const node = app.graph.add(type);
      if (!node) throw new Error(`Failed to create ${type}`);
      node.pos = [x, y];
      createdNodes.push(node.id);
      return node;
    };

    // Create workflow
    const checkpoint = addNode("CheckpointLoaderSimple", 0, 0);
    const ksampler = addNode("KSampler", 300, 0);
    const vae = addNode("VAEDecode", 600, 0);
    const save = addNode("SaveImage", 900, 0);

    // Connect nodes
    checkpoint.connect(0, ksampler, 0); // MODEL
    checkpoint.connect(1, ksampler, 2); // CLIP (to positive)
    checkpoint.connect(1, ksampler, 3); // CLIP (to negative)
    checkpoint.connect(2, vae, 1);      // VAE
    ksampler.connect(0, vae, 0);        // LATENT
    vae.connect(0, save, 0);            // IMAGE

    app.graph.setDirtyCanvas(true, true);

    return {
      success: true,
      data: {
        nodesCreated: createdNodes.length,
        nodeIds: createdNodes
      }
    };
  } catch (error) {
    return { success: false, error: String(error) };
  }
}
```

### Pattern 3: Tool with Async Operations

```typescript
export async function executeExecuteWorkflow(
  params: ExecuteWorkflowParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context;
  
  if (!app?.graph) {
    return { success: false, error: "App not available" };
  }

  try {
    // Queue the workflow
    await app.queuePrompt();

    // Wait a bit to get the prompt ID
    await new Promise(resolve => setTimeout(resolve, 100));

    return {
      success: true,
      data: {
        queued: true,
        message: "Workflow queued for execution"
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Failed to queue workflow"
    };
  }
}
```

## Backend Examples

### Complete Backend Integration

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

# __init__.py - Handler
async def chat_api_handler(request: web.Request) -> web.Response:
    body = await request.json()
    messages = body.get("messages", [])
    
    # Convert to OpenAI format
    openai_messages = _ui_messages_to_openai(messages)
    
    # Call API with tools
    stream = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=openai_messages,
        tools=TOOLS,
        stream=True,
    )
    
    # Stream response
    resp = web.StreamResponse(status=200, headers=UI_MESSAGE_STREAM_HEADERS)
    await resp.prepare(request)
    
    async for chunk in stream:
        # ... handle streaming
        pass
    
    return resp
```

## Real Conversation Examples

### Example 1: Basic Node Addition

```
User: "Add a KSampler node"

LLM: [Calls addNode tool]
{
  "nodeType": "KSampler"
}

Result:
{
  "success": true,
  "data": {
    "nodeId": 5,
    "nodeType": "KSampler",
    "position": [0, 0]
  }
}

LLM Response: "I've added a KSampler node to your workflow (Node ID: 5)."
```

### Example 2: Workflow Modification

```
User: "Add a checkpoint loader at position 100, 50 and connect it to the KSampler"

LLM: [Calls addNode tool]
{
  "nodeType": "CheckpointLoaderSimple",
  "position": { "x": 100, "y": 50 }
}

Result: { "success": true, "data": { "nodeId": 6 } }

LLM: [Calls connectNodes tool]
{
  "sourceNodeId": 6,
  "sourceSlot": 0,
  "targetNodeId": 5,
  "targetSlot": 0
}

Result: { "success": true, "data": { "linkId": 3 } }

LLM Response: "I've added a CheckpointLoaderSimple node at position (100, 50) and connected its MODEL output to the KSampler's model input."
```

### Example 3: Workflow Query

```
User: "What nodes do I have in my workflow?"

LLM: [Calls getWorkflowInfo tool]
{}

Result:
{
  "success": true,
  "data": {
    "nodeCount": 3,
    "nodes": [
      { "id": 5, "type": "KSampler", "position": [0, 0] },
      { "id": 6, "type": "CheckpointLoaderSimple", "position": [100, 50] },
      { "id": 7, "type": "SaveImage", "position": [300, 0] }
    ],
    "nodeTypes": {
      "KSampler": 1,
      "CheckpointLoaderSimple": 1,
      "SaveImage": 1
    }
  }
}

LLM Response: "Your workflow has 3 nodes:
- KSampler (Node 5)
- CheckpointLoaderSimple (Node 6)
- SaveImage (Node 7)"
```

## Testing Examples

```typescript
// Test tool execution
describe('executeAddNode', () => {
  it('should add a node successfully', async () => {
    const mockApp = {
      graph: {
        add: jest.fn().mockReturnValue({
          id: 1,
          pos: [0, 0],
          title: "KSampler"
        }),
        setDirtyCanvas: jest.fn()
      }
    };

    const result = await executeAddNode(
      { nodeType: "KSampler" },
      { app: mockApp as any }
    );

    expect(result.success).toBe(true);
    expect(result.data?.nodeId).toBe(1);
    expect(mockApp.graph.setDirtyCanvas).toHaveBeenCalled();
  });
});
```

## Next Steps

- Review [architecture.md](./architecture.md) for system design
- Check [implementation.md](./implementation.md) for setup
- See [definitions.md](./definitions.md) for schema patterns
- Read [backend-integration.md](./backend-integration.md) for API details
