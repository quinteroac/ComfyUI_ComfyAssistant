/**
 * Hook to register ComfyUI tools in the assistant-ui runtime.
 *
 * Uses useAssistantTool to add each tool to the runtime's ModelContext.
 * The runtime automatically executes tools when the LLM issues tool-call
 * parts, sends results back via addToolResult, and resubmits for the
 * next LLM response — no manual interception or text-based hacks needed.
 */
import { useAssistantTool } from '@assistant-ui/react'

import {
  addNodeDefinition,
  connectNodesDefinition,
  fillPromptNodeDefinition,
  getWorkflowInfoDefinition,
  removeNodeDefinition,
  setNodeWidgetValueDefinition
} from '@/tools/definitions'
import {
  executeAddNode,
  executeConnectNodes,
  executeFillPromptNode,
  executeGetWorkflowInfo,
  executeRemoveNode,
  executeSetNodeWidgetValue
} from '@/tools/implementations'
import type { ToolContext } from '@/tools/types'

/**
 * Returns a ToolContext backed by window.app, or null if unavailable.
 */
function getToolContext(): ToolContext | null {
  if (!window.app) return null
  return { app: window.app }
}

/**
 * Registers all ComfyUI agentic tools into the assistant runtime.
 *
 * Must be called inside an AssistantRuntimeProvider tree.
 * The number of hook calls is fixed (one per tool), satisfying Rules of Hooks.
 */
export function useComfyTools() {
  useAssistantTool({
    toolName: addNodeDefinition.name,
    description: addNodeDefinition.description,
    parameters: addNodeDefinition.parameters,
    execute: async (args) => {
      const ctx = getToolContext()
      if (!ctx) return { success: false, error: 'ComfyUI app is not available' }
      return executeAddNode(args, ctx)
    }
  })

  useAssistantTool({
    toolName: removeNodeDefinition.name,
    description: removeNodeDefinition.description,
    parameters: removeNodeDefinition.parameters,
    execute: async (args) => {
      const ctx = getToolContext()
      if (!ctx) return { success: false, error: 'ComfyUI app is not available' }
      return executeRemoveNode(args, ctx)
    }
  })

  useAssistantTool({
    toolName: connectNodesDefinition.name,
    description: connectNodesDefinition.description,
    parameters: connectNodesDefinition.parameters,
    execute: async (args) => {
      const ctx = getToolContext()
      if (!ctx) return { success: false, error: 'ComfyUI app is not available' }
      return executeConnectNodes(args, ctx)
    }
  })

  useAssistantTool({
    toolName: getWorkflowInfoDefinition.name,
    description: getWorkflowInfoDefinition.description,
    parameters: getWorkflowInfoDefinition.parameters,
    execute: async (args) => {
      const ctx = getToolContext()
      if (!ctx) return { success: false, error: 'ComfyUI app is not available' }
      return executeGetWorkflowInfo(args, ctx)
    }
  })

  useAssistantTool({
    toolName: setNodeWidgetValueDefinition.name,
    description: setNodeWidgetValueDefinition.description,
    parameters: setNodeWidgetValueDefinition.parameters,
    execute: async (args) => {
      const ctx = getToolContext()
      if (!ctx) return { success: false, error: 'ComfyUI app is not available' }
      return executeSetNodeWidgetValue(args, ctx)
    }
  })

  useAssistantTool({
    toolName: fillPromptNodeDefinition.name,
    description: fillPromptNodeDefinition.description,
    parameters: fillPromptNodeDefinition.parameters,
    execute: async (args) => {
      const ctx = getToolContext()
      if (!ctx) return { success: false, error: 'ComfyUI app is not available' }
      return executeFillPromptNode(args, ctx)
    }
  })
}
