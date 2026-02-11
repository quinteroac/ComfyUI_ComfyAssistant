import type { WebSearchParams } from '../definitions/web-search'
import type { ToolResult } from '../types'

/**
 * Result of a web search
 */
interface WebSearchResult {
  results: Array<{
    title: string
    url: string
    snippet: string
  }>
  provider: string
  query: string
}

/**
 * Implementation of the webSearch tool.
 * Calls the backend API to perform a web search.
 */
export async function executeWebSearch(
  params: WebSearchParams
): Promise<ToolResult<WebSearchResult>> {
  try {
    const response = await fetch('/api/research/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: params.query,
        maxResults: params.maxResults,
        timeRange: params.timeRange
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
        results: data.results,
        provider: data.provider,
        query: data.query
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
