import type { SearchNodeRegistryParams } from '../definitions/search-node-registry'
import type { ToolResult } from '../types'

/**
 * Result of searching the ComfyUI node registry
 */
interface SearchNodeRegistryResult {
  nodes: Array<{
    id: string
    name: string
    author: string
    description: string
    downloads: number
    repository: string
    tags: string[]
  }>
  total: number
  page: number
  totalPages: number
}

/**
 * Implementation of the searchNodeRegistry tool.
 * Calls the backend API to search the ComfyUI Registry.
 */
export async function executeSearchNodeRegistry(
  params: SearchNodeRegistryParams
): Promise<ToolResult<SearchNodeRegistryResult>> {
  try {
    const queryParams = new URLSearchParams()
    queryParams.set('q', params.query)
    if (params.limit) queryParams.set('limit', String(params.limit))
    if (params.page) queryParams.set('page', String(params.page))

    const response = await fetch(
      `/api/research/registry?${queryParams.toString()}`
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
      data: {
        nodes: data.nodes,
        total: data.total,
        page: data.page,
        totalPages: data.totalPages
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
