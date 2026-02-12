import type { ToolResult } from '../types'

/**
 * One skill in the list (slug, name, description)
 */
interface SkillSummary {
  slug: string
  name: string
  description: string
}

/**
 * Result of listing user skills
 */
interface ListUserSkillsResult {
  skills: SkillSummary[]
}

/**
 * Lists all user skills (slug, name, description) from the backend.
 */
export async function executeListUserSkills(): Promise<
  ToolResult<ListUserSkillsResult>
> {
  try {
    const response = await fetch('/api/user-context/skills')
    const data = await response.json()

    if (!response.ok) {
      return {
        success: false,
        error: data.error || `Server error: ${response.status}`
      }
    }

    const skills = (data.skills ?? []).map(
      (s: { slug: string; name: string; description?: string }) => ({
        slug: s.slug,
        name: s.name,
        description: s.description ?? ''
      })
    )

    return {
      success: true,
      data: { skills }
    }
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'Failed to list skills'
    }
  }
}
