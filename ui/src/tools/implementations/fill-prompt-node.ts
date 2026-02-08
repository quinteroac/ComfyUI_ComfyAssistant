import type { FillPromptNodeParams } from '../definitions/fill-prompt-node'
import type { ToolContext, ToolResult } from '../types'
import { executeSetNodeWidgetValue } from './set-node-widget-value'

/**
 * Implementation of the tool for filling a prompt node's text.
 * Thin wrapper around setNodeWidgetValue with widgetName='text'.
 */
export async function executeFillPromptNode(
  params: FillPromptNodeParams,
  context: ToolContext
): Promise<ToolResult> {
  const { app } = context

  if (!app?.graph) {
    return {
      success: false,
      error: 'ComfyUI app is not available'
    }
  }

  // Validate node exists before delegating
  const node = app.graph.getNodeById(params.nodeId)
  if (!node) {
    return {
      success: false,
      error: `Node with ID ${params.nodeId} not found`
    }
  }

  return executeSetNodeWidgetValue(
    { nodeId: params.nodeId, widgetName: 'text', value: params.text },
    context
  )
}
