import { z } from 'zod'

/**
 * Parameter schema for updating a user skill
 */
export const updateSkillSchema = z.object({
  slug: z.string().describe('The slug of the skill to update'),
  name: z
    .string()
    .optional()
    .describe('Optional new human-readable name for the skill'),
  description: z.string().optional().describe('Optional new brief description'),
  instructions: z
    .string()
    .optional()
    .describe('Optional new full instructions (replaces existing)')
})

/**
 * Tool definition for updating a user skill
 */
export const updateSkillDefinition = {
  name: 'updateSkill',
  description:
    'Updates an existing user skill by slug. Use when the user wants to change the name, description, or instructions of a skill they created earlier. Provide only the fields to change.',
  parameters: updateSkillSchema
}

export type UpdateSkillParams = z.infer<typeof updateSkillSchema>
