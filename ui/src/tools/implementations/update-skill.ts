import type { UpdateSkillParams } from '../definitions/update-skill'
import type { ToolResult } from '../types'

/**
 * Result of updating a skill
 */
interface UpdateSkillResult {
  slug: string
  name: string
  description: string
}

/**
 * Implementation of the updateSkill tool.
 * Calls the backend API to update the skill.
 */
export async function executeUpdateSkill(
  params: UpdateSkillParams
): Promise<ToolResult<UpdateSkillResult>> {
  try {
    const slug = encodeURIComponent(params.slug)
    const body: Record<string, string> = {}
    if (params.name !== undefined) body.name = params.name
    if (params.description !== undefined) body.description = params.description
    if (params.instructions !== undefined) body.instructions = params.instructions

    const response = await fetch(`/api/user-context/skills/${slug}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body)
    })

    const data = await response.json()

    if (response.status === 404) {
      return {
        success: false,
        error: data.error || `Skill '${params.slug}' not found`
      }
    }

    if (!response.ok) {
      return {
        success: false,
        error: data.error || `Server error: ${response.status}`
      }
    }

    const skill = data.skill ?? data
    return {
      success: true,
      data: {
        slug: skill.slug ?? params.slug,
        name: skill.name ?? '',
        description: skill.description ?? ''
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
