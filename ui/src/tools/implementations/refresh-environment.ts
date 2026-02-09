import type { ToolResult } from '../types'

/**
 * Result of refreshing the environment
 */
interface RefreshEnvironmentResult {
  node_types_count: number
  custom_packages_count: number
  models_count: number
  model_categories: Record<string, number>
}

/**
 * Implementation of the refreshEnvironment tool.
 * Calls the backend API to trigger a full environment scan.
 */
export async function executeRefreshEnvironment(): Promise<
  ToolResult<RefreshEnvironmentResult>
> {
  try {
    const response = await fetch('/api/environment/scan', {
      method: 'POST'
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
      data: data.summary
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
