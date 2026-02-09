import { z } from 'zod'

/**
 * Parameter schema for removing a node
 */
export const removeNodeSchema = z.object({
  nodeId: z.number().describe('ID of the node to remove')
})

/**
 * Tool definition for removing nodes
 */
export const removeNodeDefinition = {
  name: 'removeNode',
  description: 'Removes an existing node from the ComfyUI workflow by its ID.',
  parameters: removeNodeSchema
}

export type RemoveNodeParams = z.infer<typeof removeNodeSchema>
