import { z } from 'zod'

/**
 * No parameters for listing skills
 */
export const listUserSkillsSchema = z.object({})

/**
 * Tool definition for listing user skills (slug, name, description)
 */
export const listUserSkillsDefinition = {
  name: 'listUserSkills',
  description:
    "Lists the user's saved skills (slug, name, description). Use this to see which skills exist before loading one with getUserSkill(slug) when the user refers to a preference or you need to apply a remembered instruction.",
  parameters: listUserSkillsSchema
}

export type ListUserSkillsParams = z.infer<typeof listUserSkillsSchema>
