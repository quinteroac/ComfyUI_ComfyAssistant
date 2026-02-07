import { z } from 'zod';

/**
 * Parameter schema for adding a node
 */
export const addNodeSchema = z.object({
  nodeType: z.string().describe("Node type to add (e.g., 'KSampler', 'CheckpointLoaderSimple', 'LoadImage')"),
  position: z.object({
    x: z.number().describe("X coordinate on the canvas"),
    y: z.number().describe("Y coordinate on the canvas")
  }).optional().describe("Optional node position on the canvas. If not specified, adds at default position")
});

/**
 * Tool definition for adding nodes
 */
export const addNodeDefinition = {
  name: "addNode",
  description: "Adds a new node to the ComfyUI workflow. Allows specifying the node type and optionally its position on the canvas.",
  parameters: addNodeSchema,
};

export type AddNodeParams = z.infer<typeof addNodeSchema>;
