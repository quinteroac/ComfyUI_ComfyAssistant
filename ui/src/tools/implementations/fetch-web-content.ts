import type { FetchWebContentParams } from '../definitions/fetch-web-content'
import type { ToolResult } from '../types'

/**
 * Result of fetching web content
 */
interface FetchWebContentResult {
  content: string
  detectedWorkflows: Array<Record<string, unknown>>
  metadata: {
    url: string
    provider: string
    truncated: boolean
    contentLength: number
  }
}

/**
 * Implementation of the fetchWebContent tool.
 * Calls the backend API to fetch and extract content from a URL.
 */
export async function executeFetchWebContent(
  params: FetchWebContentParams
): Promise<ToolResult<FetchWebContentResult>> {
  try {
    const response = await fetch('/api/research/fetch', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        url: params.url,
        extractWorkflow: params.extractWorkflow
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
        content: data.content,
        detectedWorkflows: data.detectedWorkflows,
        metadata: data.metadata
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
