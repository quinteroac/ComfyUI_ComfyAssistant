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
  createSkillDefinition,
  deleteSkillDefinition,
  updateSkillDefinition,
  fillPromptNodeDefinition,
  getAvailableModelsDefinition,
  getWorkflowInfoDefinition,
  readDocumentationDefinition,
  refreshEnvironmentDefinition,
  removeNodeDefinition,
  searchInstalledNodesDefinition,
  setNodeWidgetValueDefinition
} from '@/tools/definitions'
import {
  executeAddNode,
  executeConnectNodes,
  executeCreateSkill,
  executeDeleteSkill,
  executeUpdateSkill,
  executeFillPromptNode,
  executeGetAvailableModels,
  executeGetWorkflowInfo,
  executeReadDocumentation,
  executeRefreshEnvironment,
  executeRemoveNode,
  executeSearchInstalledNodes,
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

  useAssistantTool({
    toolName: createSkillDefinition.name,
    description: createSkillDefinition.description,
    parameters: createSkillDefinition.parameters,
    execute: async (args) => {
      return executeCreateSkill(args)
    }
  })

  useAssistantTool({
    toolName: deleteSkillDefinition.name,
    description: deleteSkillDefinition.description,
    parameters: deleteSkillDefinition.parameters,
    execute: async (args) => {
      return executeDeleteSkill(args)
    }
  })

  useAssistantTool({
    toolName: updateSkillDefinition.name,
    description: updateSkillDefinition.description,
    parameters: updateSkillDefinition.parameters,
    execute: async (args) => {
      return executeUpdateSkill(args)
    }
  })

  useAssistantTool({
    toolName: refreshEnvironmentDefinition.name,
    description: refreshEnvironmentDefinition.description,
    parameters: refreshEnvironmentDefinition.parameters,
    execute: async () => {
      return executeRefreshEnvironment()
    }
  })

  useAssistantTool({
    toolName: searchInstalledNodesDefinition.name,
    description: searchInstalledNodesDefinition.description,
    parameters: searchInstalledNodesDefinition.parameters,
    execute: async (args) => {
      return executeSearchInstalledNodes(args)
    }
  })

  useAssistantTool({
    toolName: readDocumentationDefinition.name,
    description: readDocumentationDefinition.description,
    parameters: readDocumentationDefinition.parameters,
    execute: async (args) => {
      return executeReadDocumentation(args)
    }
  })

  useAssistantTool({
    toolName: getAvailableModelsDefinition.name,
    description: getAvailableModelsDefinition.description,
    parameters: getAvailableModelsDefinition.parameters,
    execute: async (args) => {
      return executeGetAvailableModels(args)
    }
  })
}
