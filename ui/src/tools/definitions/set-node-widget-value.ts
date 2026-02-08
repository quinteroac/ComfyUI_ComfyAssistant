import { z } from 'zod'

/**
 * Parameter schema for setting a node widget value
 */
export const setNodeWidgetValueSchema = z.object({
  nodeId: z.number().describe('ID of the node whose widget to set'),
  widgetName: z
    .string()
    .describe(
      "Name of the widget (e.g., 'steps', 'cfg', 'seed', 'text', 'sampler_name')"
    ),
  value: z
    .union([
      z.string(),
      z.number(),
      z.boolean(),
      z.array(z.union([z.string(), z.number(), z.boolean()]))
    ])
    .describe('New value for the widget (pass a single value, not an array)')
})

/**
 * Tool definition for setting a node widget value
 */
export const setNodeWidgetValueDefinition = {
  name: 'setNodeWidgetValue',
  description:
    'Sets the value of a widget (parameter) on a node. Use getWorkflowInfo with includeNodeDetails first to see available widget names and their current values.',
  parameters: setNodeWidgetValueSchema
}

export type SetNodeWidgetValueParams = z.infer<typeof setNodeWidgetValueSchema>
