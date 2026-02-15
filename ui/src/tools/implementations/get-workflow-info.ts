import type { GetWorkflowInfoParams } from '../definitions/get-workflow-info'
import type { ToolContext, ToolResult } from '../types'

/**
 * Widget information exposed when includeNodeDetails is true
 */
interface WidgetInfo {
  name: string
  type?: string
  value: unknown
  options?: string[]
}

/**
 * Summary information of a node
 */
interface NodeInfo {
  id: string | number
  type: string
  title?: string
  position?: [number, number]
  size?: [number, number]
  widgets?: WidgetInfo[]
}

/**
 * Information about a connection between nodes
 */
interface ConnectionInfo {
  sourceNodeId: string | number
  sourceSlot: number
  sourceSlotName?: string
  targetNodeId: string | number
  targetSlot: number
  targetSlotName?: string
}

/** Full workflow in frontend format (nodes + links), as returned by graphToPrompt */
interface FullWorkflowPayload {
  nodes: unknown[]
  links: unknown[]
  [key: string]: unknown
}

/** API-format workflow (node IDs -> { class_type, inputs }) */
interface ApiWorkflowPayload {
  [nodeId: string]: { class_type: string; inputs: Record<string, unknown> }
}

/**
 * Result of getting workflow information
 */
interface WorkflowInfo {
  nodeCount: number
  nodes: NodeInfo[]
  connections: ConnectionInfo[]
  canvasSize?: { width: number; height: number }
  fullWorkflow?: FullWorkflowPayload
  apiWorkflow?: ApiWorkflowPayload
  fullFormatError?: string
}

/**
 * Implementation of the tool for getting workflow information.
 *
 * Returns a compact representation by default (no layout, no widget options).
 * Use includeLayout=true for position/size, includeWidgetOptions=true for
 * combo option lists, includeNodeDetails=true for widget names+values, and
 * fullFormat=true for the complete workflow in frontend and API format.
 */
export async function executeGetWorkflowInfo(
  params: GetWorkflowInfoParams,
  context: ToolContext
): Promise<ToolResult<WorkflowInfo>> {
  const { app } = context

  if (!app?.graph) {
    return {
      success: false,
      error: 'ComfyUI app is not available'
    }
  }

  try {
    const nodes: NodeInfo[] = []
    const connections: ConnectionInfo[] = []
    const includeLayout = params.includeLayout ?? false
    const includeWidgetOptions = params.includeWidgetOptions ?? false

    // Collect node information
    for (const node of app.graph._nodes) {
      const nodeInfo: NodeInfo = {
        id: node.id,
        type: node.type
      }

      // Layout info is opt-in (rarely needed for reasoning)
      if (includeLayout) {
        nodeInfo.position = node.pos as [number, number]
      }

      if (params.includeNodeDetails) {
        if (includeLayout) {
          nodeInfo.size = node.size as [number, number]
        }
        nodeInfo.title = node.title

        // Populate widget info (filter out non-configurable widgets like buttons)
        if (node.widgets) {
          const widgets: WidgetInfo[] = []
          for (const widget of node.widgets) {
            if (widget.type === 'button') continue
            const info: WidgetInfo = {
              name: widget.name,
              value: widget.value
            }
            // Include widget type only when options are requested (gives context)
            if (includeWidgetOptions) {
              info.type = widget.type
              // Expose available options for combo/dropdown widgets
              const opts = (widget as any).options?.values
              if (widget.type === 'combo' && Array.isArray(opts)) {
                info.options = opts
              }
            }
            widgets.push(info)
          }
          if (widgets.length > 0) {
            nodeInfo.widgets = widgets
          }
        }
      }

      nodes.push(nodeInfo)

      // Collect connections (outputs) with slot names for better reasoning
      if (node.outputs) {
        for (let i = 0; i < node.outputs.length; i++) {
          const output = node.outputs[i]
          if (output.links) {
            for (const linkId of output.links) {
              const link = app.graph.links[linkId]
              if (link) {
                const connInfo: ConnectionInfo = {
                  sourceNodeId: node.id,
                  sourceSlot: i,
                  targetNodeId: link.target_id,
                  targetSlot: link.target_slot
                }
                // Add slot names for better LLM reasoning
                if (output.name) {
                  connInfo.sourceSlotName = output.name
                }
                const targetNode = app.graph.getNodeById(link.target_id)
                if (targetNode?.inputs?.[link.target_slot]?.name) {
                  connInfo.targetSlotName =
                    targetNode.inputs[link.target_slot].name
                }
                connections.push(connInfo)
              }
            }
          }
        }
      }
    }

    const result: WorkflowInfo = {
      nodeCount: nodes.length,
      nodes,
      connections
    }

    // Canvas size is layout info — only include when requested
    if (includeLayout && app.canvas) {
      result.canvasSize = {
        width: app.canvas.canvas.width,
        height: app.canvas.canvas.height
      }
    }

    // Full format: include workflow in frontend and API form for applyWorkflowJson or detailed analysis
    if (params.fullFormat === true && typeof app.graphToPrompt === 'function') {
      try {
        const { workflow, output } = await app.graphToPrompt(app.graph, {})
        result.fullWorkflow = workflow as FullWorkflowPayload
        result.apiWorkflow = output as ApiWorkflowPayload
      } catch (fullErr) {
        result.fullFormatError =
          fullErr instanceof Error ? fullErr.message : String(fullErr)
      }
    }

    return {
      success: true,
      data: result
    }
  } catch (error) {
    return {
      success: false,
      error:
        error instanceof Error
          ? error.message
          : 'Unknown error getting workflow information'
    }
  }
}
