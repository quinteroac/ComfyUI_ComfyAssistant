import type { ReadDocumentationParams } from '../definitions/read-documentation'
import type { ToolResult } from '../types'

/**
 * Result of reading documentation
 */
interface ReadDocumentationResult {
  topic: string
  source: string
  content: string
  node_info: Record<string, unknown> | null
}

/**
 * Implementation of the readDocumentation tool.
 * Calls the backend API to resolve documentation for a topic.
 */
export async function executeReadDocumentation(
  params: ReadDocumentationParams
): Promise<ToolResult<ReadDocumentationResult>> {
  try {
    const queryParams = new URLSearchParams()
    queryParams.set('topic', params.topic)
    if (params.source) queryParams.set('source', params.source)

    const response = await fetch(
      `/api/environment/docs?${queryParams.toString()}`
    )
    const data = await response.json()

    if (!response.ok) {
      return {
        success: false,
        error: data.error || `Server error: ${response.status}`
      }
    }

    return {
      success: true,
      data: data
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
