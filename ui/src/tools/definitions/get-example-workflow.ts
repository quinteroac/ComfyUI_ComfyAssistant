import { z } from 'zod'

export const getExampleWorkflowSchema = z.object({
  category: z.enum([
    'flux',
    'flux2',
    'lumina2',
    'qwen_image',
    'sdxl',
    'wan',
    'wan22',
    'z_image'
  ]),
  query: z.string().optional(),
  maxResults: z.number().optional()
})

export const getExampleWorkflowDefinition = {
  name: 'getExampleWorkflow',
  description:
    'Fetches example workflows extracted from the ComfyUI_examples repository for a specific model category.',
  parameters: getExampleWorkflowSchema
}

export type GetExampleWorkflowParams = z.infer<typeof getExampleWorkflowSchema>
