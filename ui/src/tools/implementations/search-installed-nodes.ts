import type { SearchInstalledNodesParams } from '../definitions/search-installed-nodes'
import type { ToolResult } from '../types'

/**
 * Result of searching installed nodes
 */
interface SearchInstalledNodesResult {
  nodes: Array<{
    name: string
    category: string
    package: string
  }>
  count: number
}

/**
 * Implementation of the searchInstalledNodes tool.
 * Calls the backend API to search cached node data.
 */
const DEBUG_PREFIX = '[ComfyAssistant searchInstalledNodes]'

export async function executeSearchInstalledNodes(
  params: SearchInstalledNodesParams
): Promise<ToolResult<SearchInstalledNodesResult>> {
  try {
    const queryParams = new URLSearchParams()
    if (params.query) queryParams.set('q', params.query)
    if (params.category) queryParams.set('category', params.category)
    if (params.limit) queryParams.set('limit', String(params.limit))

    const url = `/api/environment/nodes?${queryParams.toString()}`
    if (typeof console !== 'undefined' && console.debug) {
      console.debug(DEBUG_PREFIX, 'params', params, 'url', url)
    }

    const response = await fetch(url)
    const data = await response.json()

    if (typeof console !== 'undefined' && console.debug) {
      console.debug(DEBUG_PREFIX, 'response', {
        ok: response.ok,
        status: response.status,
        count: data?.count,
        nodesLength: data?.nodes?.length,
        error: data?.error
      })
    }

    if (!response.ok) {
      return {
        success: false,
        error: data.error || `Server error: ${response.status}`
      }
    }

    return {
      success: true,
      data: {
        nodes: data.nodes,
        count: data.count
      }
    }
  } catch (error) {
    if (typeof console !== 'undefined' && console.debug) {
      console.debug(DEBUG_PREFIX, 'error', error)
    }
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
