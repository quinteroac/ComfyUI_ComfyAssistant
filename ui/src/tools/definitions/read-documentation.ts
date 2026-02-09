import { z } from 'zod'

/**
 * Parameter schema for reading documentation
 */
export const readDocumentationSchema = z.object({
  topic: z
    .string()
    .describe(
      "Topic to look up documentation for (e.g., 'KSampler', 'ControlNet', 'comfyui_impact_pack')"
    ),
  source: z
    .enum(['installed', 'builtin', 'any'])
    .optional()
    .describe(
      "Where to search: 'installed' (custom nodes), 'builtin' (system docs), or 'any' (default: 'any')"
    )
})

/**
 * Tool definition for reading documentation
 */
export const readDocumentationDefinition = {
  name: 'readDocumentation',
  description:
    "Fetches documentation for a node type, custom node package, or topic. Returns node inputs/outputs, README excerpts, and any available documentation.",
  parameters: readDocumentationSchema
}

export type ReadDocumentationParams = z.infer<typeof readDocumentationSchema>
