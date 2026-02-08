import { z } from 'zod'

/**
 * Parameter schema for filling a prompt node's text
 */
export const fillPromptNodeSchema = z.object({
  nodeId: z
    .number()
    .describe('ID of the CLIPTextEncode (or similar prompt) node'),
  text: z.string().describe('The prompt text to set')
})

/**
 * Tool definition for filling a prompt node
 */
export const fillPromptNodeDefinition = {
  name: 'fillPromptNode',
  description:
    "Sets the text of a prompt node (CLIPTextEncode). Shorthand for setNodeWidgetValue with widgetName='text'.",
  parameters: fillPromptNodeSchema
}

export type FillPromptNodeParams = z.infer<typeof fillPromptNodeSchema>
