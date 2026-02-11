import type { GetExampleWorkflowParams } from '../definitions/get-example-workflow'
import type { ToolResult } from '../types'

interface ExampleWorkflowResult {
  category: string
  query: string
  count: number
  results: Array<{
    source: string
    workflow: Record<string, unknown> | null
    workflowFormat: 'api' | 'graph' | 'unknown'
    displayNames: Record<string, string>
    titleTypeMap: Record<string, string>
    image?: string
    file?: string
    workflowGraph?: Record<string, unknown>
  }>
}

/**
 * Implementation of the getExampleWorkflow tool.
 * Calls the backend API to fetch extracted ComfyUI_examples workflows.
 */
export async function executeGetExampleWorkflow(
  params: GetExampleWorkflowParams
): Promise<ToolResult<ExampleWorkflowResult>> {
  try {
    const response = await fetch('/api/research/examples', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        category: params.category,
        query: params.query,
        maxResults: params.maxResults
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
        category: data.category,
        query: data.query,
        count: data.count,
        results: data.results
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
