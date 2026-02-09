import type { ConnectNodesParams } from '../definitions/connect-nodes'
import type { ToolContext, ToolResult } from '../types'

/**
 * Result of connecting nodes
 */
interface ConnectNodesResult {
  sourceNodeId: number
  sourceSlot: number
  targetNodeId: number
  targetSlot: number
  linkId: string | number
}

/**
 * Implementation of the tool for connecting nodes
 */
export async function executeConnectNodes(
  params: ConnectNodesParams,
  context: ToolContext
): Promise<ToolResult<ConnectNodesResult>> {
  const { app } = context

  if (!app?.graph) {
    return {
      success: false,
      error: 'ComfyUI app is not available'
    }
  }

  try {
    // Find the nodes
    const sourceNode = app.graph.getNodeById(params.sourceNodeId)
    const targetNode = app.graph.getNodeById(params.targetNodeId)

    if (!sourceNode) {
      return {
        success: false,
        error: `Source node with ID ${params.sourceNodeId} not found`
      }
    }

    if (!targetNode) {
      return {
        success: false,
        error: `Target node with ID ${params.targetNodeId} not found`
      }
    }

    // Validate that the slots exist
    if (!sourceNode.outputs || params.sourceSlot >= sourceNode.outputs.length) {
      return {
        success: false,
        error: `Source node does not have an output slot at index ${params.sourceSlot}`
      }
    }

    if (!targetNode.inputs || params.targetSlot >= targetNode.inputs.length) {
      return {
        success: false,
        error: `Target node does not have an input slot at index ${params.targetSlot}`
      }
    }

    // Connect the nodes
    const linkId = sourceNode.connect(
      params.sourceSlot,
      targetNode,
      params.targetSlot
    )

    if (linkId === null || linkId === undefined) {
      return {
        success: false,
        error: 'Could not create connection. Data types might be incompatible.'
      }
    }

    // Update the canvas
    app.graph.setDirtyCanvas(true, true)

    return {
      success: true,
      data: {
        sourceNodeId: params.sourceNodeId,
        sourceSlot: params.sourceSlot,
        targetNodeId: params.targetNodeId,
        targetSlot: params.targetSlot,
        linkId: linkId as any
      }
    }
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error
          ? error.message
          : 'Unknown error connecting nodes'
    }
  }
}
