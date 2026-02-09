import { z } from 'zod'

/**
 * Parameter schema for deleting a user skill
 */
export const deleteSkillSchema = z.object({
  slug: z
    .string()
    .describe(
      "The slug of the skill to delete (e.g. 'use-preview-image', 'prefer-sdxl-models')"
    )
})

/**
 * Tool definition for deleting a user skill
 */
export const deleteSkillDefinition = {
  name: 'deleteSkill',
  description:
    "Deletes a user skill by its slug. Use when the user asks to forget a preference, remove a remembered skill, or delete a specific skill. The slug is the identifier used in the skills list (e.g. 'use-preview-image').",
  parameters: deleteSkillSchema
}

export type DeleteSkillParams = z.infer<typeof deleteSkillSchema>
