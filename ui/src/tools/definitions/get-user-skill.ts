import { z } from 'zod'

/**
 * Parameter schema for loading a user skill by slug
 */
export const getUserSkillSchema = z.object({
  slug: z
    .string()
    .describe(
      "The slug of the skill to load (e.g. 'use-preview-image', 'prefer-sdxl-models')"
    )
})

/**
 * Tool definition for loading a user skill's instructions on demand
 */
export const getUserSkillDefinition = {
  name: 'getUserSkill',
  description:
    "Loads a user skill's full instructions by slug. Use after listUserSkills when the user refers to a saved preference or when you need to apply a remembered skill. Returns slug, name, description, and instructions.",
  parameters: getUserSkillSchema
}

export type GetUserSkillParams = z.infer<typeof getUserSkillSchema>
