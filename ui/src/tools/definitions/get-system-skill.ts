import { z } from 'zod'

export const getSystemSkillSchema = z.object({
  slug: z
    .string()
    .describe(
      "The slug of the system skill (e.g. '09_model_flux', '13_model_sdxl')"
    )
})

/**
 * Tool definition for loading a model-specific system skill by slug (on demand)
 */
export const getSystemSkillDefinition = {
  name: 'getSystemSkill',
  description:
    'Loads a model-specific system skill by slug (e.g. 09_model_flux, 13_model_sdxl). Call after listSystemSkills when the user asks about a model or a workflow for a model; match the model name to the skill and load it before answering or creating the workflow. Returns slug, name, and full content to apply.',
  parameters: getSystemSkillSchema
}

export type GetSystemSkillParams = z.infer<typeof getSystemSkillSchema>
