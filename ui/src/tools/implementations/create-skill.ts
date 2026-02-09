import type { CreateSkillParams } from '../definitions/create-skill'
import type { ToolResult } from '../types'

/**
 * Result of creating a skill
 */
interface CreateSkillResult {
  slug: string
  name: string
  description: string
}

/**
 * Implementation of the createSkill tool.
 * Calls the backend API to persist the skill.
 */
export async function executeCreateSkill(
  params: CreateSkillParams
): Promise<ToolResult<CreateSkillResult>> {
  try {
    const response = await fetch('/api/user-context/skills', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: params.name,
        description: params.description,
        instructions: params.instructions
      })
    })

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
        slug: data.skill.slug,
        name: data.skill.name,
        description: data.skill.description
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
