import { z } from 'zod'

export const listSystemSkillsSchema = z.object({})

/**
 * Tool definition for listing model-specific system skills (on demand)
 */
export const listSystemSkillsDefinition = {
  name: 'listSystemSkills',
  description:
    'Lists model-specific system skills (Flux, SDXL, Lumina2, etc.) available on demand. Returns slug and name. When the user asks about a model or a workflow for a model, call this first to find the matching skill, then getSystemSkill(slug) to load it before answering or building the workflow.',
  parameters: listSystemSkillsSchema
}

export type ListSystemSkillsParams = z.infer<typeof listSystemSkillsSchema>
