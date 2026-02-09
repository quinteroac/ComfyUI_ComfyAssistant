import { z } from 'zod'

/**
 * Parameter schema for refreshing the environment
 */
export const refreshEnvironmentSchema = z.object({})

/**
 * Tool definition for refreshing the environment scan
 */
export const refreshEnvironmentDefinition = {
  name: 'refreshEnvironment',
  description:
    'Rescans the ComfyUI installation to update the list of installed node types, custom node packages, and available models. Use after installing new custom nodes or models, or when the user asks about their environment.',
  parameters: refreshEnvironmentSchema
}

export type RefreshEnvironmentParams = z.infer<
  typeof refreshEnvironmentSchema
>
