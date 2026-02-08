import type { SetNodeWidgetValueParams } from '../definitions/set-node-widget-value'
import type { ToolContext, ToolResult } from '../types'

/**
 * Result of setting a widget value
 */
interface SetWidgetResult {
  nodeId: number
  widgetName: string
  previousValue: unknown
  newValue: unknown
}

/**
 * Implementation of the tool for setting a node widget value
 */
export async function executeSetNodeWidgetValue(
  params: SetNodeWidgetValueParams,
  context: ToolContext
): Promise<ToolResult<SetWidgetResult>> {
  const { app } = context

  if (!app?.graph) {
    return {
      success: false,
      error: 'ComfyUI app is not available'
    }
  }

  try {
    const node = app.graph.getNodeById(params.nodeId)
    if (!node) {
      return {
        success: false,
        error: `Node with ID ${params.nodeId} not found`
      }
    }

    if (!node.widgets || node.widgets.length === 0) {
      return {
        success: false,
        error: `Node ${params.nodeId} (${node.type}) has no widgets`
      }
    }

    // Find the widget by name
    const widget = node.widgets.find((w: any) => w.name === params.widgetName)

    if (!widget) {
      const availableNames = node.widgets
        .filter((w: any) => w.type !== 'button')
        .map((w: any) => w.name)
      return {
        success: false,
        error: `Widget "${params.widgetName}" not found on node ${params.nodeId} (${node.type}). Available widgets: ${availableNames.join(', ')}`
      }
    }

    // Unwrap array values (some LLMs send ["value"] instead of "value" for combo widgets)
    const resolvedValue = Array.isArray(params.value) ? params.value[0] : params.value

    const previousValue = widget.value
    widget.value = resolvedValue

    // Trigger widget callbacks so the node updates properly
    if (typeof widget.callback === 'function') {
      widget.callback(resolvedValue)
    }
    if (typeof (node as any).onWidgetChanged === 'function') {
      ;(node as any).onWidgetChanged(
        params.widgetName,
        resolvedValue,
        previousValue,
        widget
      )
    }

    app.graph.setDirtyCanvas(true, true)

    return {
      success: true,
      data: {
        nodeId: params.nodeId,
        widgetName: params.widgetName,
        previousValue,
        newValue: resolvedValue
      }
    }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
