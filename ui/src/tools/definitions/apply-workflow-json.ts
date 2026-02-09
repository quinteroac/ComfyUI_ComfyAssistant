import { z } from 'zod'

/**
 * Schema for a single node in the ComfyUI API format.
 */
const apiNodeSchema = z.object({
  class_type: z.string(),
  inputs: z.record(z.string(), z.any()),
  _meta: z
    .object({
      title: z.string()
    })
    .optional()
})

/**
 * Parameter schema for loading a complete API-format workflow.
 * Keys are string node IDs, values describe each node.
 */
export const applyWorkflowJsonSchema = z.object({
  workflow: z.record(z.string(), apiNodeSchema)
})

/**
 * Tool definition for loading a complete workflow from API JSON
 */
export const applyWorkflowJsonDefinition = {
  name: 'applyWorkflowJson',
  description:
    'Loads a complete ComfyUI workflow in API format, replacing the current graph. Use for complex multi-node workflows that would take many addNode/connectNodes calls. The workflow object keys are string node IDs; values have class_type, inputs (scalar values or [nodeId, outputIndex] links), and optional _meta.title.',
  parameters: applyWorkflowJsonSchema
}

export type ApplyWorkflowJsonParams = z.infer<typeof applyWorkflowJsonSchema>
