import type { GetSystemSkillParams } from '../definitions/get-system-skill'
import type { ToolResult } from '../types'

interface GetSystemSkillResult {
  slug: string
  name: string
  content: string
}

/**
 * Loads a model-specific system skill by slug from the backend (on demand).
 */
export async function executeGetSystemSkill(
  params: GetSystemSkillParams
): Promise<ToolResult<GetSystemSkillResult>> {
  try {
    const slug = encodeURIComponent(params.slug)
    const response = await fetch(`/api/system-context/skills/${slug}`)
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
        name: data.name ?? data.slug,
        content: data.content ?? ''
      }
    }
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'Failed to load system skill'
    }
  }
}
