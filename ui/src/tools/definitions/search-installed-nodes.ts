import { z } from 'zod'

/**
 * Parameter schema for searching installed nodes
 */
export const searchInstalledNodesSchema = z.object({
  query: z
    .string()
    .describe(
      "Search term to match against node name, category, or package (e.g., 'upscale', 'KSampler', 'impact')"
    ),
  category: z
    .string()
    .optional()
    .describe(
      "Filter by node category (e.g., 'sampling', 'image', 'conditioning')"
    ),
  limit: z
    .number()
    .optional()
    .describe('Maximum number of results to return (default: 20)')
})

/**
 * Tool definition for searching installed nodes
 */
export const searchInstalledNodesDefinition = {
  name: 'searchInstalledNodes',
  description:
    "Searches installed node types in the user's ComfyUI installation. Use to find available nodes by name, category, or package. If no results, try refreshEnvironment first.",
  parameters: searchInstalledNodesSchema
}

export type SearchInstalledNodesParams = z.infer<
  typeof searchInstalledNodesSchema
>
