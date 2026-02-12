import type { ToolResult } from '../types'

interface SkillSummary {
  slug: string
  name: string
}

interface ListSystemSkillsResult {
  skills: SkillSummary[]
}

/**
 * Lists model-specific system skills from the backend (on demand).
 */
export async function executeListSystemSkills(): Promise<
  ToolResult<ListSystemSkillsResult>
> {
  try {
    const response = await fetch('/api/system-context/skills')
    const data = await response.json()

    if (!response.ok) {
      return {
        success: false,
        error: data.error || `Server error: ${response.status}`
      }
    }

    const skills = (data.skills ?? []).map(
      (s: { slug: string; name: string }) => ({
        slug: s.slug,
        name: s.name ?? s.slug
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
        error instanceof Error ? error.message : 'Failed to list system skills'
    }
  }
}
