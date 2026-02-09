import type { DeleteSkillParams } from '../definitions/delete-skill'
import type { ToolResult } from '../types'

/**
 * Result of deleting a skill
 */
interface DeleteSkillResult {
  slug: string
}

/**
 * Implementation of the deleteSkill tool.
 * Calls the backend API to remove the skill.
 */
export async function executeDeleteSkill(
  params: DeleteSkillParams
): Promise<ToolResult<DeleteSkillResult>> {
  try {
    const slug = encodeURIComponent(params.slug)
    const response = await fetch(`/api/user-context/skills/${slug}`, {
      method: 'DELETE'
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

    return {
      success: true,
      data: { slug: data.slug ?? params.slug }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
