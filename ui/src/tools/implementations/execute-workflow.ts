import type { ExecuteWorkflowParams } from '../definitions/execute-workflow'
import type { ToolContext, ToolResult } from '../types'

const DEFAULT_TIMEOUT_S = 300

interface OutputInfo {
  nodeId: string
  images?: Array<{ filename: string; subfolder: string; type: string }>
}

interface ExecuteWorkflowResult {
  status: 'success' | 'error' | 'interrupted' | 'timeout'
  promptId: string
  executionTimeMs: number
  outputs: OutputInfo[]
  error?: string
}

/**
 * Queues the current workflow for execution, waits for completion,
 * and returns the status and output summary.
 */
export async function executeExecuteWorkflow(
  params: ExecuteWorkflowParams,
  context: ToolContext
): Promise<ToolResult<ExecuteWorkflowResult>> {
  const { app } = context

  if (!app?.graph) {
    return {
      success: false,
      error: 'ComfyUI app is not available'
    }
  }

  const timeoutMs = (params.timeout ?? DEFAULT_TIMEOUT_S) * 1000

  try {
    // Serialize the graph to prompt data
    console.log('[ExecuteWorkflow] Serializing graph...')
    const promptData = await app.graphToPrompt()

    // Collect outputs as nodes complete
    const outputs: OutputInfo[] = []
    const startTime = Date.now()
    let promptId = ''

    const result = await new Promise<ExecuteWorkflowResult>((resolve) => {
      let resolved = false

      // eslint-disable-next-line prefer-const -- must declare before cleanup references it
      let timeoutHandle: ReturnType<typeof setTimeout>

      const cleanup = () => {
        if (resolved) return
        resolved = true
        clearTimeout(timeoutHandle)
        app.api.removeEventListener('executed', onExecuted)
        app.api.removeEventListener('execution_success', onSuccess)
        app.api.removeEventListener('execution_error', onError)
        app.api.removeEventListener('execution_interrupted', onInterrupted)
      }

      const onExecuted = (event: CustomEvent) => {
        const detail = event.detail
        if (!detail) return
        // Filter by prompt_id
        if (detail.prompt_id && detail.prompt_id !== promptId) return

        const output: OutputInfo = {
          nodeId: String(detail.node ?? detail.display_node ?? '')
        }
        if (detail.output?.images) {
          output.images = detail.output.images
        }
        outputs.push(output)
      }

      const onSuccess = (event: CustomEvent) => {
        const detail = event.detail
        if (detail?.prompt_id && detail.prompt_id !== promptId) return
        cleanup()
        resolve({
          status: 'success',
          promptId,
          executionTimeMs: Date.now() - startTime,
          outputs
        })
      }

      const onError = (event: CustomEvent) => {
        const detail = event.detail
        if (detail?.prompt_id && detail.prompt_id !== promptId) return
        cleanup()
        resolve({
          status: 'error',
          promptId,
          executionTimeMs: Date.now() - startTime,
          outputs,
          error: detail?.exception_message
            ? `${detail.node_type ?? 'Unknown node'}: ${detail.exception_message}`
            : 'Execution failed with unknown error'
        })
      }

      const onInterrupted = (event: CustomEvent) => {
        const detail = event.detail
        // execution_interrupted may lack prompt_id — accept it regardless
        if (detail?.prompt_id && detail.prompt_id !== promptId) return
        cleanup()
        resolve({
          status: 'interrupted',
          promptId,
          executionTimeMs: Date.now() - startTime,
          outputs
        })
      }

      // Attach listeners BEFORE queueing to avoid race condition
      app.api.addEventListener('executed', onExecuted)
      app.api.addEventListener('execution_success', onSuccess)
      app.api.addEventListener('execution_error', onError)
      app.api.addEventListener('execution_interrupted', onInterrupted)

      // Set timeout
      timeoutHandle = setTimeout(() => {
        cleanup()
        resolve({
          status: 'timeout',
          promptId,
          executionTimeMs: Date.now() - startTime,
          outputs
        })
      }, timeoutMs)

      // Queue the prompt
      console.log('[ExecuteWorkflow] Queueing prompt...')
      app.api
        .queuePrompt(0, promptData)
        .then((response) => {
          promptId = response.prompt_id
          console.log('[ExecuteWorkflow] Prompt queued with id:', promptId)

          // Check for immediate validation errors
          if (
            response.node_errors &&
            Object.keys(response.node_errors).length > 0
          ) {
            cleanup()
            const errorNodes = Object.keys(response.node_errors)
            resolve({
              status: 'error',
              promptId,
              executionTimeMs: Date.now() - startTime,
              outputs: [],
              error: `Validation errors on nodes: ${errorNodes.join(', ')}. Check node connections and inputs.`
            })
          }
        })
        .catch((err: unknown) => {
          cleanup()
          resolve({
            status: 'error',
            promptId: '',
            executionTimeMs: Date.now() - startTime,
            outputs: [],
            error: err instanceof Error ? err.message : String(err)
          })
        })
    })

    console.log('[ExecuteWorkflow] Execution result:', result.status)
    return { success: true, data: result }
  } catch (error) {
    console.error('[ExecuteWorkflow] Error:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    }
  }
}
