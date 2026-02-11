import { z } from 'zod'

/**
 * Parameter schema for web search
 */
export const webSearchSchema = z.object({
  query: z
    .string()
    .describe(
      "Search query (e.g., 'ComfyUI ControlNet tutorial', 'SDXL inpainting workflow')"
    ),
  maxResults: z
    .number()
    .optional()
    .describe('Maximum number of results to return (default: 5, max: 20)'),
  timeRange: z
    .enum(['day', 'week', 'month', 'year'])
    .optional()
    .describe(
      "Optional time filter for recency (e.g., 'week' for results from the last week)"
    )
})

/**
 * Tool definition for web search
 */
export const webSearchDefinition = {
  name: 'webSearch',
  description:
    'Searches the web for ComfyUI-related information, tutorials, workflows, documentation, and custom node guides.',
  parameters: webSearchSchema
}

export type WebSearchParams = z.infer<typeof webSearchSchema>
