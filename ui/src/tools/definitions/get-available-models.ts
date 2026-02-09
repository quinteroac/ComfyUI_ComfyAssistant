import { z } from 'zod'

/**
 * Parameter schema for listing available models
 */
export const getAvailableModelsSchema = z.object({
  category: z
    .string()
    .optional()
    .describe(
      "Filter by model category (e.g. 'checkpoints', 'loras', 'vae', 'embeddings'). If omitted, returns all categories."
    )
})

/**
 * Tool definition for listing available models
 */
export const getAvailableModelsDefinition = {
  name: 'getAvailableModels',
  description:
    "Lists the user's installed model filenames by category (checkpoints, loras, vae, etc.). Use when the user asks for model recommendations (e.g. 'what do you recommend for hyperrealistic?', 'which checkpoint for anime?') so you can suggest specific models they have.",
  parameters: getAvailableModelsSchema
}

export type GetAvailableModelsParams = z.infer<
  typeof getAvailableModelsSchema
>
