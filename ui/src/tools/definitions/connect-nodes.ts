import { z } from 'zod';

/**
 * Parameter schema for connecting nodes
 */
export const connectNodesSchema = z.object({
  sourceNodeId: z.number().describe("ID of the source node"),
  sourceSlot: z.number().describe("Output slot index of the source node"),
  targetNodeId: z.number().describe("ID of the target node"),
  targetSlot: z.number().describe("Input slot index of the target node")
});

/**
 * Tool definition for connecting nodes
 */
export const connectNodesDefinition = {
  name: "connectNodes",
  description: "Connects two nodes in the ComfyUI workflow. Creates a connection from an output slot of one node to an input slot of another node.",
  parameters: connectNodesSchema,
};

export type ConnectNodesParams = z.infer<typeof connectNodesSchema>;
