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

/** API format: keys are node IDs, values have class_type and inputs. */
const apiWorkflowSchema = z.record(z.string(), apiNodeSchema)

/**
 * Frontend (graph) format: object with nodes array and links array.
 * Used by ComfyUI templates and exported workflows.
 */
const frontendWorkflowSchema = z
  .object({
    nodes: z.array(z.any()),
    links: z.array(z.any())
  })
  .passthrough()

/**
 * Parameter schema: workflow can be API format or frontend format.
 */
export const applyWorkflowJsonSchema = z.object({
  workflow: z.union([apiWorkflowSchema, frontendWorkflowSchema])
})

/**
 * Tool definition for loading a complete workflow from JSON.
 * Accepts either API format (node IDs -> { class_type, inputs }) or
 * frontend format (nodes array + links array, as from templates or export).
 */
export const applyWorkflowJsonDefinition = {
  name: 'applyWorkflowJson',
  description:
    'Loads a complete ComfyUI workflow, replacing the current graph. Accepts two formats: (1) API format: object with string node IDs as keys and values { class_type, inputs, optional _meta.title }. (2) Frontend format: object with nodes (array) and links (array), as exported by ComfyUI or returned by official/custom templates. Use for complex workflows that would take many addNode/connectNodes calls.',
  parameters: applyWorkflowJsonSchema
}

export type ApplyWorkflowJsonParams = z.infer<typeof applyWorkflowJsonSchema>
