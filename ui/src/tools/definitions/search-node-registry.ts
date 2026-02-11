import { z } from 'zod'

/**
 * Parameter schema for searching the ComfyUI node registry
 */
export const searchNodeRegistrySchema = z.object({
  query: z
    .string()
    .describe("Search term (e.g., 'face detection', 'upscale', 'controlnet')"),
  limit: z
    .number()
    .optional()
    .describe('Maximum results per page (default: 10, max: 50)'),
  page: z
    .number()
    .optional()
    .describe('Page number for pagination (default: 1)')
})

/**
 * Tool definition for searching the node registry
 */
export const searchNodeRegistryDefinition = {
  name: 'searchNodeRegistry',
  description:
    'Searches the ComfyUI Registry for custom node packages by name, description, or tags.',
  parameters: searchNodeRegistrySchema
}

export type SearchNodeRegistryParams = z.infer<typeof searchNodeRegistrySchema>
