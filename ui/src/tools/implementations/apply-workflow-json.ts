import type { ApplyWorkflowJsonParams } from '../definitions/apply-workflow-json'
import type { ToolContext, ToolResult } from '../types'

interface ApplyWorkflowJsonResult {
  nodeCount: number
  nodeTypes: string[]
  referencedModels: string[]
  warnings?: string[]
}

interface FrontendWorkflow {
  nodes: Array<{ id?: number | string; type?: string; widgets_values?: unknown[]; properties?: { models?: Array<{ name?: string }> } }>
  links: unknown[]
}

function isFrontendFormat(workflow: unknown): workflow is FrontendWorkflow {
  return (
    typeof workflow === 'object' &&
    workflow !== null &&
    Array.isArray((workflow as FrontendWorkflow).nodes) &&
    Array.isArray((workflow as FrontendWorkflow).links)
  )
}

function isApiFormat(
  workflow: unknown
): workflow is Record<string, { class_type: string; inputs: Record<string, unknown>; _meta?: { title?: string } }> {
  if (typeof workflow !== 'object' || workflow === null) return false
  const w = workflow as Record<string, unknown>
  if (Array.isArray((workflow as FrontendWorkflow).nodes)) return false
  const keys = Object.keys(w)
  if (keys.length === 0) return false
  return keys.every((id) => {
    const node = w[id]
    return (
      node &&
      typeof node === 'object' &&
      typeof (node as { class_type?: string }).class_type === 'string' &&
      (node as { inputs?: unknown }).inputs !== undefined
    )
  })
}

/**
 * Fetches workflow JSON from temp file API by id.
 */
async function fetchWorkflowFromTemp(workflowPath: string): Promise<unknown> {
  const url = `/api/temp/file?id=${encodeURIComponent(workflowPath)}`
  const res = await fetch(url)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.error ?? `Failed to fetch temp file: ${res.status}`)
  }
  return res.json()
}

/**
 * Validates node types and loads a complete workflow (API or frontend format),
 * replacing the current graph. Supports inline workflow or workflowPath (temp file id).
 */
export async function executeApplyWorkflowJson(
  params: ApplyWorkflowJsonParams,
  context: ToolContext
): Promise<ToolResult<ApplyWorkflowJsonResult>> {
  const { app } = context

  if (!app?.graph) {
    return {
      success: false,
      error: 'ComfyUI app is not available'
    }
  }

  let workflow: unknown = params.workflow

  if (params.workflowPath) {
    try {
      workflow = await fetchWorkflowFromTemp(params.workflowPath)
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Failed to load workflow from temp file'
      }
    }
  }

  if (!workflow) {
    return {
      success: false,
      error: 'Either workflow or workflowPath is required'
    }
  }

  if (isFrontendFormat(workflow)) {
    return loadFrontendWorkflow(workflow, app)
  }

  if (isApiFormat(workflow)) {
    return loadApiWorkflow(workflow, app)
  }

  return {
    success: false,
    error:
      'Unknown workflow format: expected API format (node IDs -> { class_type, inputs }) or frontend format (nodes array + links array).'
  }
}

async function loadFrontendWorkflow(
  workflow: FrontendWorkflow,
  app: NonNullable<ToolContext['app']>
): Promise<ToolResult<ApplyWorkflowJsonResult>> {
  if (workflow.nodes.length === 0) {
    return {
      success: false,
      error: 'Workflow is empty — no nodes provided'
    }
  }

  try {
    await app.loadGraphData(workflow as Parameters<typeof app.loadGraphData>[0], true, true, null, {
      showMissingNodesDialog: true,
      showMissingModelsDialog: true
    })
    app.graph.setDirtyCanvas(true, true)

    const nodeTypes = [...new Set(workflow.nodes.map((n) => n.type).filter(Boolean))] as string[]
    const referencedModels: string[] = []
    for (const node of workflow.nodes) {
      if (node.properties?.models?.length) {
        for (const m of node.properties.models) {
          if (m.name) referencedModels.push(m.name)
        }
      }
      const vals = node.widgets_values
      if (Array.isArray(vals)) {
        for (const v of vals) {
          if (typeof v === 'string' && v.includes('.') && /\.(safetensors|ckpt|pt|bin)$/i.test(v)) {
            referencedModels.push(v)
          }
        }
      }
    }

    console.log('[ApplyWorkflowJson] Workflow loaded successfully (frontend format)')
    return {
      success: true,
      data: {
        nodeCount: workflow.nodes.length,
        nodeTypes,
        referencedModels: [...new Set(referencedModels)]
      }
    }
  } catch (error) {
    console.error('[ApplyWorkflowJson] Error:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}

const modelWidgetNames = [
  'ckpt_name',
  'vae_name',
  'lora_name',
  'model_name',
  'unet_name',
  'clip_name',
  'diffusion_model',
  'style_model'
]

async function loadApiWorkflow(
  workflow: Record<string, { class_type: string; inputs: Record<string, unknown>; _meta?: { title?: string } }>,
  app: NonNullable<ToolContext['app']>
): Promise<ToolResult<ApplyWorkflowJsonResult>> {
  const nodeIds = Object.keys(workflow)

  if (nodeIds.length === 0) {
    return {
      success: false,
      error: 'Workflow is empty — no nodes provided'
    }
  }

  try {
    const warnings: string[] = []
    const LiteGraph = (window as unknown as { LiteGraph?: { registered_node_types?: Record<string, unknown> } }).LiteGraph
    const referencedModels: string[] = []

    if (LiteGraph?.registered_node_types) {
      for (const nodeId of nodeIds) {
        const node = workflow[nodeId]
        if (node.class_type && !LiteGraph.registered_node_types[node.class_type]) {
          warnings.push(`Node ${nodeId}: unknown type "${node.class_type}" — it may not be installed`)
        }
        if (node.inputs) {
          for (const [key, value] of Object.entries(node.inputs)) {
            if (
              modelWidgetNames.some((name) => key.includes(name)) &&
              typeof value === 'string' &&
              value.includes('.')
            ) {
              referencedModels.push(value)
            }
          }
        }
      }
    }

    const apiData: Record<
      string,
      { class_type: string; inputs: Record<string, unknown>; _meta: { title: string } }
    > = {}
    for (const nodeId of nodeIds) {
      const node = workflow[nodeId]
      apiData[nodeId] = {
        class_type: node.class_type,
        inputs: node.inputs,
        _meta: {
          title: node._meta?.title ?? node.class_type
        }
      }
    }

    app.loadApiJson(apiData, 'assistant-workflow.json')
    app.graph.setDirtyCanvas(true, true)

    const nodeTypes = [...new Set(nodeIds.map((id) => workflow[id].class_type))]

    console.log('[ApplyWorkflowJson] Workflow loaded successfully (API format)')
    return {
      success: true,
      data: {
        nodeCount: nodeIds.length,
        nodeTypes,
        referencedModels: [...new Set(referencedModels)],
        ...(warnings.length > 0 ? { warnings } : {})
      }
    }
  } catch (error) {
    console.error('[ApplyWorkflowJson] Error:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
