import type { ComfyApp } from '@comfyorg/comfyui-frontend-types'
import { z } from 'zod'

/**
 * Context that all tools receive to access the ComfyUI API
 */
export interface ToolContext {
  app: ComfyApp
}

/**
 * Base definition for a tool
 */
export interface ToolDefinition<TParams extends z.ZodSchema> {
  name: string
  description: string
  parameters: TParams
  execute: (params: z.infer<TParams>, context: ToolContext) => Promise<unknown>
}

/**
 * Generic result of a tool operation
 */
export interface ToolResult<T = unknown> {
  success: boolean
  data?: T
  error?: string
}
