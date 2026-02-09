import { z } from 'zod'

/**
 * Parameter schema for creating a user skill
 */
export const createSkillSchema = z.object({
  name: z
    .string()
    .describe(
      "Short, descriptive name for the skill (e.g., 'Use Preview Image', 'Prefer SDXL models')"
    ),
  description: z
    .string()
    .describe('Brief description of what this skill does'),
  instructions: z
    .string()
    .describe(
      'Full instructions for the assistant to follow when this skill is active'
    )
})

/**
 * Tool definition for creating a user skill
 */
export const createSkillDefinition = {
  name: 'createSkill',
  description:
    "Creates a persistent user skill (a remembered instruction or preference). Use when the user says 'remember to...', 'always do...', 'from now on...', etc. The skill will be applied in future conversations.",
  parameters: createSkillSchema
}

export type CreateSkillParams = z.infer<typeof createSkillSchema>
