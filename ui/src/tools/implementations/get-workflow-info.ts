import type { ToolContext, ToolResult } from '../types';
import type { GetWorkflowInfoParams } from '../definitions/get-workflow-info';

/**
 * Summary information of a node
 */
interface NodeInfo {
  id: string | number;
  type: string;
  position: [number, number];
  size?: [number, number];
  title?: string;
}

/**
 * Information about a connection between nodes
 */
interface ConnectionInfo {
  sourceNodeId: string | number;
  sourceSlot: number;
  targetNodeId: string | number;
  targetSlot: number;
}

/**
 * Result of getting workflow information
 */
interface WorkflowInfo {
  nodeCount: number;
  nodes: NodeInfo[];
  connections: ConnectionInfo[];
  canvasSize?: { width: number; height: number };
}

/**
 * Implementation of the tool for getting workflow information
 */
export async function executeGetWorkflowInfo(
  params: GetWorkflowInfoParams,
  context: ToolContext
): Promise<ToolResult<WorkflowInfo>> {
  const { app } = context;
  
  if (!app?.graph) {
    return {
      success: false,
      error: "ComfyUI app is not available"
    };
  }

  try {
    const nodes: NodeInfo[] = [];
    const connections: ConnectionInfo[] = [];

    // Collect node information
    for (const node of app.graph._nodes) {
      const nodeInfo: NodeInfo = {
        id: node.id,
        type: node.type,
        position: node.pos as [number, number],
      };

      if (params.includeNodeDetails) {
        nodeInfo.size = node.size as [number, number];
        nodeInfo.title = node.title;
      }

      nodes.push(nodeInfo);

      // Collect connections (outputs)
      if (node.outputs) {
        for (let i = 0; i < node.outputs.length; i++) {
          const output = node.outputs[i];
          if (output.links) {
            for (const linkId of output.links) {
              const link = app.graph.links[linkId];
              if (link) {
                connections.push({
                  sourceNodeId: node.id,
                  sourceSlot: i,
                  targetNodeId: link.target_id,
                  targetSlot: link.target_slot
                });
              }
            }
          }
        }
      }
    }

    return {
      success: true,
      data: {
        nodeCount: nodes.length,
        nodes,
        connections,
        canvasSize: app.canvas ? {
          width: app.canvas.canvas.width,
          height: app.canvas.canvas.height
        } : undefined
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : "Unknown error getting workflow information"
    };
  }
}
