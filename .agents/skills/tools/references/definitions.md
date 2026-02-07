# Tool Definitions Guide

How to create effective tool definitions using Zod schemas and clear descriptions.

## Anatomy of a Tool Definition

```typescript
import { z } from 'zod';

// 1. Schema - Defines parameters and validation
export const myToolSchema = z.object({
  param1: z.string().describe("What this parameter does"),
  param2: z.number().optional().describe("Optional parameter"),
});

// 2. Definition - Metadata for the tool
export const myToolDefinition = {
  name: "myTool",
  description: "Clear, detailed description of what the tool does",
  parameters: myToolSchema,
};

// 3. Type - TypeScript type derived from schema
export type MyToolParams = z.infer<typeof myToolSchema>;
```

## Schema Best Practices

### Use Descriptive `.describe()`

The LLM reads these descriptions to understand parameters:

```typescript
// ❌ Bad - No description
z.string()

// ✅ Good - Clear description
z.string().describe("Node type to add (e.g., 'KSampler', 'LoadImage')")
```

### Provide Examples in Descriptions

```typescript
z.string().describe("Node type to add. Examples: 'KSampler', 'CheckpointLoaderSimple', 'LoadImage'")
```

### Use Appropriate Types

```typescript
// Strings for identifiers/names
nodeType: z.string()

// Numbers for IDs/counts/coordinates
nodeId: z.number()
x: z.number()

// Booleans for flags
includeDetails: z.boolean()

// Objects for structured data
position: z.object({
  x: z.number(),
  y: z.number()
})

// Arrays for lists
nodeIds: z.array(z.number())

// Enums for fixed choices
operation: z.enum(["add", "remove", "update"])
```

### Mark Optional Parameters

```typescript
// Required parameter
nodeType: z.string()

// Optional parameter
position: z.object({ x: z.number(), y: z.number() }).optional()

// Optional with default
includeDetails: z.boolean().optional().default(false)
```

### Use Constraints

```typescript
// String constraints
nodeType: z.string().min(1).max(100)

// Number constraints
x: z.number().int().min(0)
opacity: z.number().min(0).max(1)

// Array constraints
nodeIds: z.array(z.number()).min(1).max(10)
```

## Tool Name Guidelines

### Naming Convention

Use camelCase for consistency with JavaScript:

```typescript
// ✅ Good
"addNode"
"removeNode"
"connectNodes"
"getWorkflowInfo"

// ❌ Bad
"add_node"
"AddNode"
"add-node"
```

### Verb-Noun Pattern

Start with an action verb:

```typescript
// ✅ Good
"addNode"        // verb + noun
"removeNode"     // verb + noun
"setNodeWidget"  // verb + noun
"getWorkflowInfo" // verb + noun

// ❌ Bad
"node"           // unclear action
"workflow"       // unclear action
"nodeAdder"      // awkward
```

### Be Specific

```typescript
// ✅ Good
"addKSamplerNode"      // specific
"connectNodesBySlot"   // specific

// ⚠️  Less ideal (but acceptable)
"addNode"              // generic but flexible
"connectNodes"         // generic but flexible
```

## Description Guidelines

### Template Structure

```typescript
description: "[Action] [object] [context/details]. [Optional: constraints/examples]"
```

### Examples

```typescript
// ✅ Excellent
description: "Adds a new node to the ComfyUI workflow. Allows specifying the node type and optionally its position on the canvas. Use this when the user wants to add a node like KSampler, LoadImage, etc."

// ✅ Good
description: "Removes an existing node from the ComfyUI workflow by its ID."

// ⚠️  Acceptable
description: "Adds a node to the workflow"

// ❌ Too vague
description: "Adds a node"
```

### Include Context

Help the LLM understand when to use the tool:

```typescript
description: "Gets information about the current ComfyUI workflow, including the list of nodes, connections, and general configuration. Use this when the user asks about the current state of their workflow, node counts, or wants to understand the workflow structure."
```

### Mention Capabilities and Limitations

```typescript
description: "Connects two nodes in the ComfyUI workflow. Creates a connection from an output slot of one node to an input slot of another node. Note: The connection will fail if the data types are incompatible."
```

## Complete Examples

### Example 1: Simple Tool

```typescript
import { z } from 'zod';

export const clearWorkflowSchema = z.object({
  confirm: z.boolean().describe("Confirmation flag to prevent accidental deletion")
});

export const clearWorkflowDefinition = {
  name: "clearWorkflow",
  description: "Clears all nodes from the current ComfyUI workflow. This is a destructive action that removes everything. Requires confirmation flag to be true.",
  parameters: clearWorkflowSchema,
};

export type ClearWorkflowParams = z.infer<typeof clearWorkflowSchema>;
```

### Example 2: Complex Tool

```typescript
import { z } from 'zod';

export const addNodeSchema = z.object({
  nodeType: z.string()
    .describe("Type of node to add. Common types: 'KSampler', 'CheckpointLoaderSimple', 'LoadImage', 'SaveImage', 'CLIPTextEncode'"),
  
  position: z.object({
    x: z.number().describe("X coordinate on the canvas (pixels from left)"),
    y: z.number().describe("Y coordinate on the canvas (pixels from top)")
  }).optional()
    .describe("Optional position on the canvas. If not specified, the node will be added at the default position"),
  
  title: z.string().optional()
    .describe("Optional custom title for the node. If not specified, uses the default title based on node type"),
});

export const addNodeDefinition = {
  name: "addNode",
  description: "Adds a new node to the ComfyUI workflow. Allows specifying the node type and optionally its position and custom title. This is the primary tool for building workflows programmatically.",
  parameters: addNodeSchema,
};

export type AddNodeParams = z.infer<typeof addNodeSchema>;
```

### Example 3: Query Tool

```typescript
import { z } from 'zod';

export const getWorkflowInfoSchema = z.object({
  includeNodeDetails: z.boolean()
    .optional()
    .default(false)
    .describe("If true, includes full details of each node (size, widgets, connections). If false (default), returns only basic info for faster responses"),
  
  filterByType: z.string()
    .optional()
    .describe("Optional filter to only include nodes of a specific type (e.g., 'KSampler')")
});

export const getWorkflowInfoDefinition = {
  name: "getWorkflowInfo",
  description: "Gets information about the current ComfyUI workflow, including the list of nodes, their types, positions, and connections. Use this to answer questions about the current state of the workflow, count nodes, or understand the workflow structure before making modifications.",
  parameters: getWorkflowInfoSchema,
};

export type GetWorkflowInfoParams = z.infer<typeof getWorkflowInfoSchema>;
```

### Example 4: Enum-Based Tool

```typescript
import { z } from 'zod';

export const modifyNodeSchema = z.object({
  nodeId: z.number().describe("ID of the node to modify"),
  
  operation: z.enum(["move", "resize", "rename"])
    .describe("Type of modification: 'move' changes position, 'resize' changes size, 'rename' changes title"),
  
  value: z.union([
    z.object({ x: z.number(), y: z.number() }),  // for move
    z.object({ width: z.number(), height: z.number() }),  // for resize
    z.string()  // for rename
  ]).describe("Value for the operation. For 'move': {x, y} coordinates. For 'resize': {width, height}. For 'rename': new title string"),
});

export const modifyNodeDefinition = {
  name: "modifyNode",
  description: "Modifies an existing node in the ComfyUI workflow. Can move the node to a new position, resize it, or change its title. Choose the appropriate operation type and provide the corresponding value.",
  parameters: modifyNodeSchema,
};

export type ModifyNodeParams = z.infer<typeof modifyNodeSchema>;
```

## Backend Mapping

Zod schemas must map to OpenAI function calling format:

### TypeScript (Frontend)

```typescript
export const addNodeSchema = z.object({
  nodeType: z.string().describe("Node type to add"),
  position: z.object({
    x: z.number(),
    y: z.number()
  }).optional()
});
```

### Python (Backend)

```python
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
```

### Type Mapping

| Zod | OpenAI JSON Schema |
|-----|-------------------|
| `z.string()` | `{"type": "string"}` |
| `z.number()` | `{"type": "number"}` |
| `z.boolean()` | `{"type": "boolean"}` |
| `z.object({})` | `{"type": "object", "properties": {}}` |
| `z.array(z.string())` | `{"type": "array", "items": {"type": "string"}}` |
| `z.enum(["a", "b"])` | `{"type": "string", "enum": ["a", "b"]}` |
| `.optional()` | Omit from `"required"` array |
| `.describe("...")` | `"description": "..."` |

## Validation Examples

### Validating Tool Definitions

```typescript
// Test that schema works
const testParams = {
  nodeType: "KSampler",
  position: { x: 100, y: 200 }
};

const result = addNodeSchema.safeParse(testParams);

if (result.success) {
  console.log("Valid:", result.data);
} else {
  console.error("Invalid:", result.error);
}
```

### Common Validation Patterns

```typescript
// Email validation
email: z.string().email()

// URL validation
url: z.string().url()

// UUID validation
id: z.string().uuid()

// Custom validation
nodeType: z.string().refine(
  (val) => availableNodeTypes.includes(val),
  { message: "Invalid node type" }
)

// Transform/coerce
count: z.string().transform(val => parseInt(val))
```

## Testing Tool Definitions

```typescript
import { describe, it, expect } from 'jest';
import { addNodeSchema } from './add-node';

describe('addNodeSchema', () => {
  it('accepts valid minimal params', () => {
    const result = addNodeSchema.safeParse({
      nodeType: "KSampler"
    });
    expect(result.success).toBe(true);
  });
  
  it('accepts valid full params', () => {
    const result = addNodeSchema.safeParse({
      nodeType: "KSampler",
      position: { x: 100, y: 200 }
    });
    expect(result.success).toBe(true);
  });
  
  it('rejects invalid params', () => {
    const result = addNodeSchema.safeParse({
      nodeType: 123  // Should be string
    });
    expect(result.success).toBe(false);
  });
  
  it('rejects missing required params', () => {
    const result = addNodeSchema.safeParse({
      position: { x: 100, y: 200 }
      // Missing nodeType
    });
    expect(result.success).toBe(false);
  });
});
```

## Common Patterns

### Pattern 1: ID-based Selection

```typescript
z.object({
  nodeId: z.number().describe("ID of the node to operate on")
})
```

### Pattern 2: Multiple Selection

```typescript
z.object({
  nodeIds: z.array(z.number()).min(1).describe("Array of node IDs to operate on")
})
```

### Pattern 3: Optional Configuration

```typescript
z.object({
  nodeType: z.string(),
  options: z.object({
    visible: z.boolean().optional(),
    locked: z.boolean().optional(),
    color: z.string().optional()
  }).optional()
})
```

### Pattern 4: Union Types

```typescript
z.object({
  target: z.union([
    z.number(),  // Node ID
    z.string()   // Node title
  ]).describe("Target node by ID (number) or title (string)")
})
```

## Next Steps

- Implement tools following [implementation.md](./implementation.md)
- Set up backend following [backend-integration.md](./backend-integration.md)
- See real examples in [examples.md](./examples.md)
