import { z } from 'zod'

/**
 * Parameter schema for getting workflow information
 */
export const getWorkflowInfoSchema = z.object({
  includeNodeDetails: z
    .boolean()
    .optional()
    .describe(
      'If true, includes widget names and current values for each node. Defaults to false for faster responses'
    ),
  includeLayout: z
    .boolean()
    .optional()
    .describe(
      'If true, includes node position, size, and canvas dimensions. Defaults to false (layout info is rarely needed for reasoning)'
    ),
  includeWidgetOptions: z
    .boolean()
    .optional()
    .describe(
      'If true, includes available options for combo/dropdown widgets. Defaults to false to reduce payload size (option lists can be very large)'
    ),
  fullFormat: z
    .boolean()
    .optional()
    .describe(
      'If true, includes the full workflow in frontend format (nodes + links with all properties), suitable for applyWorkflowJson or detailed analysis. Defaults to false to keep responses compact.'
    )
})

/**
 * Tool definition for getting workflow information
 */
export const getWorkflowInfoDefinition = {
  name: 'getWorkflowInfo',
  description:
    'Gets information about the current ComfyUI workflow, including the list of nodes, connections, and general configuration. Use fullFormat: true when you need the complete canvas workflow (frontend format: nodes + links) for applyWorkflowJson or detailed analysis.',
  parameters: getWorkflowInfoSchema
}

export type GetWorkflowInfoParams = z.infer<typeof getWorkflowInfoSchema>
