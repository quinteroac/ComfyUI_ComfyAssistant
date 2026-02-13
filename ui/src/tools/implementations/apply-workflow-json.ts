import type { ApplyWorkflowJsonParams } from '../definitions/apply-workflow-json'
import type { ToolContext, ToolResult } from '../types'

interface ApplyWorkflowJsonResult {

  nodeCount: number

  nodeTypes: string[]

  referencedModels: string[]

  warnings?: string[]

}



/**

 * Validates node types and loads a complete API-format workflow,

 * replacing the current graph.

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



  const { workflow } = params

  const nodeIds = Object.keys(workflow)



  if (nodeIds.length === 0) {

    return {

      success: false,

      error: 'Workflow is empty — no nodes provided'

    }

  }



  try {

    const warnings: string[] = []

    const LiteGraph = (window as any).LiteGraph

    const referencedModels: string[] = []



    // Model-related widget names commonly used in ComfyUI

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



    // Pre-validate node types and extract referenced models

    if (LiteGraph?.registered_node_types) {

      for (const nodeId of nodeIds) {

        const node = workflow[nodeId]

        

        // Check node type

        if (

          node.class_type &&

          !LiteGraph.registered_node_types[node.class_type]

        ) {

          warnings.push(

            `Node ${nodeId}: unknown type "${node.class_type}" — it may not be installed`

          )

        }



        // Extract models from inputs

        if (node.inputs) {

          for (const [key, value] of Object.entries(node.inputs)) {

            if (modelWidgetNames.some(name => key.includes(name)) && typeof value === 'string' && value.includes('.')) {

              referencedModels.push(value)

            }

          }

        }

      }

    }



    // Ensure _meta.title is present

 (ComfyUI requires it)
    const apiData: Record<
      string,
      {
        class_type: string
        inputs: Record<string, unknown>
        _meta: { title: string }
      }
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

    // Load the workflow
    app.loadApiJson(apiData, 'assistant-workflow.json')
    app.graph.setDirtyCanvas(true, true)

    // Collect unique node types
    const nodeTypes = [...new Set(nodeIds.map((id) => workflow[id].class_type))]

    console.log('[ApplyWorkflowJson] Workflow loaded successfully')

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
