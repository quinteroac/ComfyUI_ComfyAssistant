import { z } from 'zod';

/**
 * Parameter schema for getting workflow information
 */
export const getWorkflowInfoSchema = z.object({
  includeNodeDetails: z.boolean().optional().describe("If true, includes full details of each node. Defaults to false for faster responses")
});

/**
 * Tool definition for getting workflow information
 */
export const getWorkflowInfoDefinition = {
  name: "getWorkflowInfo",
  description: "Gets information about the current ComfyUI workflow, including the list of nodes, connections, and general configuration.",
  parameters: getWorkflowInfoSchema,
};

export type GetWorkflowInfoParams = z.infer<typeof getWorkflowInfoSchema>;
