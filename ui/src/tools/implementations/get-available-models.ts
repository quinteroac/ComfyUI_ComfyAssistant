import type { GetAvailableModelsParams } from '../definitions/get-available-models'
import type { ToolResult } from '../types'

/**
 * Result of listing available models
 */
interface GetAvailableModelsResult {
  models: Record<string, string[]>
}

/**
 * Implementation of the getAvailableModels tool.
 * Calls the backend API to list model filenames by category.
 */
export async function executeGetAvailableModels(
  params: GetAvailableModelsParams
): Promise<ToolResult<GetAvailableModelsResult>> {
  try {
    const queryParams = new URLSearchParams()
    if (params.category) queryParams.set('category', params.category)

    const url = `/api/environment/models${queryParams.toString() ? `?${queryParams.toString()}` : ''}`
    const response = await fetch(url)
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
        models: data.models ?? {}
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
