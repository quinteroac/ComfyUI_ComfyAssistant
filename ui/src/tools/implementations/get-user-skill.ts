import type { GetUserSkillParams } from '../definitions/get-user-skill'
import type { ToolResult } from '../types'

/**
 * Result of loading a user skill
 */
interface GetUserSkillResult {
  slug: string
  name: string
  description: string
  instructions: string
}

/**
 * Loads a user skill by slug from the backend (on demand).
 */
export async function executeGetUserSkill(
  params: GetUserSkillParams
): Promise<ToolResult<GetUserSkillResult>> {
  try {
    const slug = encodeURIComponent(params.slug)
    const response = await fetch(`/api/user-context/skills/${slug}`)
    const data = await response.json()

    if (!response.ok) {
      return {
        success: false,
        error: data.error || `Server error: ${response.status}`
      }
    }

    return {
      success: true,
      data: {
        slug: data.slug,
        name: data.name,
        description: data.description ?? '',
        instructions: data.instructions ?? ''
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Failed to load skill'
    }
  }
}
