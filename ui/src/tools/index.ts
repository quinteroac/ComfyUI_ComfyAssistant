/**
 * Central registry of all tools available to the assistant
 */

import type { ToolContext } from './types';
import type { Tool } from '@assistant-ui/react';

// Import definitions
import {
  addNodeDefinition,
  removeNodeDefinition,
  getWorkflowInfoDefinition,
  connectNodesDefinition
} from './definitions';

// Import implementations
import {
  executeAddNode,
  executeRemoveNode,
  executeGetWorkflowInfo,
  executeConnectNodes
} from './implementations';

/**
 * Creates the tools object with implementations injected with context
 */
export function createTools(context: ToolContext): Record<string, Tool> {
  return {
    [addNodeDefinition.name]: {
      description: addNodeDefinition.description,
      parameters: addNodeDefinition.parameters,
      execute: async (params) => executeAddNode(params as any, context)
    },
    [removeNodeDefinition.name]: {
      description: removeNodeDefinition.description,
      parameters: removeNodeDefinition.parameters,
      execute: async (params) => executeRemoveNode(params as any, context)
    },
    [getWorkflowInfoDefinition.name]: {
      description: getWorkflowInfoDefinition.description,
      parameters: getWorkflowInfoDefinition.parameters,
      execute: async (params) => executeGetWorkflowInfo(params as any, context)
    },
    [connectNodesDefinition.name]: {
      description: connectNodesDefinition.description,
      parameters: connectNodesDefinition.parameters,
      execute: async (params) => executeConnectNodes(params as any, context)
    }
  };
}

// Re-export definitions for use in the backend
export * from './definitions';
export * from './types';
