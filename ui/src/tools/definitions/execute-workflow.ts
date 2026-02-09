import { z } from 'zod'

/**
 * Parameter schema for executing the current workflow
 */
export const executeWorkflowSchema = z.object({
  timeout: z
    .number()
    .optional()
    .describe(
      'Maximum time in seconds to wait for execution to complete (default: 300)'
    )
})

/**
 * Tool definition for executing workflows
 */
export const executeWorkflowDefinition = {
  name: 'executeWorkflow',
  description:
    'Queues the current ComfyUI workflow for execution, waits for completion, and returns the status and output summary. Use after building or modifying a workflow when the user wants to run it.',
  parameters: executeWorkflowSchema
}

export type ExecuteWorkflowParams = z.infer<typeof executeWorkflowSchema>
