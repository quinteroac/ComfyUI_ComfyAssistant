import type { RemoveNodeParams } from '../definitions/remove-node'
import type { ToolContext, ToolResult } from '../types'

/**
 * Result of removing a node
 */
interface RemoveNodeResult {
  nodeId: number
  removed: boolean
}

/**
 * Implementation of the tool for removing nodes
 */
export async function executeRemoveNode(
  params: RemoveNodeParams,
  context: ToolContext
): Promise<ToolResult<RemoveNodeResult>> {
  const { app } = context

  if (!app?.graph) {
    return {
      success: false,
      error: 'ComfyUI app is not available'
    }
  }

  try {
    // Find the node by ID
    const node = app.graph.getNodeById(params.nodeId)

    if (!node) {
      return {
        success: false,
        error: `Node with ID ${params.nodeId} not found`
      }
    }

    // Remove the node
    app.graph.remove(node)

    // Update the canvas
    app.graph.setDirtyCanvas(true, true)

    return {
      success: true,
      data: {
        nodeId: params.nodeId,
        removed: true
      }
    }
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error ? error.message : 'Unknown error removing node'
    }
  }
}
