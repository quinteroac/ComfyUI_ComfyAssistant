import { z } from 'zod'

/**
 * Parameter schema for fetching web content
 */
export const fetchWebContentSchema = z.object({
  url: z.string().describe('URL to fetch content from (must be http or https)'),
  extractWorkflow: z
    .boolean()
    .optional()
    .describe(
      'Whether to scan content for embedded ComfyUI API-format workflows (default: true)'
    )
})

/**
 * Tool definition for fetching web content
 */
export const fetchWebContentDefinition = {
  name: 'fetchWebContent',
  description:
    'Fetches and extracts content from a URL, returning text and optionally detecting embedded ComfyUI workflows.',
  parameters: fetchWebContentSchema
}

export type FetchWebContentParams = z.infer<typeof fetchWebContentSchema>
