import type { ToolContext, ToolResult } from '../types';
import type { AddNodeParams } from '../definitions/add-node';

/**
 * Result of adding a node
 */
interface AddNodeResult {
  nodeId: string | number;
  nodeType: string;
  position: [number, number];
}

/**
 * Implementation of the tool for adding nodes
 */
export async function executeAddNode(
  params: AddNodeParams,
  context: ToolContext
): Promise<ToolResult<AddNodeResult>> {
  const { app } = context;
  
  if (!app?.graph) {
    return {
      success: false,
      error: "ComfyUI app is not available"
    };
  }

  try {
    console.log('[AddNode] Attempting to add node:', params.nodeType);
    
    // Check if LiteGraph is available globally
    const LiteGraph = (window as any).LiteGraph;
    if (!LiteGraph) {
      return {
        success: false,
        error: "LiteGraph is not available. Make sure ComfyUI is loaded."
      };
    }
    
    // Create the node using LiteGraph.createNode (the correct way)
    console.log('[AddNode] Creating node with LiteGraph.createNode...');
    const node = LiteGraph.createNode(params.nodeType);
    
    if (!node) {
      return {
        success: false,
        error: `Could not create node of type: ${params.nodeType}. Verify that the node type is valid.`
      };
    }
    
    console.log('[AddNode] Node created:', node.id, node.type);

    // Add the node to the graph FIRST (before positioning)
    // This is important because the graph may initialize the node's position
    app.graph.add(node);

    // Now position the node intelligently
    if (params.position) {
      // Use specified position
      console.log('[AddNode] Using specified position:', params.position);
      node.pos = [params.position.x, params.position.y];
    } else {
      // Auto-position: find a free spot to avoid overlapping
      const SPACING_X = 250; // Horizontal spacing between nodes (increased)
      
      // Get current viewport center or use a default position
      const canvas = app.canvas;
      let baseX = 50;
      let baseY = 50;
      
      if (canvas) {
        // Use visible area center as starting point
        const visibleArea = canvas.visible_area;
        if (visibleArea) {
          baseX = visibleArea[0] + 100; // Add some margin from left edge
          baseY = visibleArea[1] + 100; // Add some margin from top edge
        }
      }
      
      // Find the rightmost node to position new nodes to the right
      let maxX = baseX;
      let maxY = baseY;
      
      for (const existingNode of app.graph._nodes) {
        if (existingNode.pos && existingNode.id !== node.id) {
          const nodeRight = existingNode.pos[0] + (existingNode.size?.[0] || 200);
          const nodeBottom = existingNode.pos[1];
          if (nodeRight > maxX) {
            maxX = nodeRight;
            maxY = nodeBottom;
          }
        }
      }
      
      // Position new node to the right with spacing
      const autoPos = [maxX + SPACING_X, maxY];
      console.log('[AddNode] Using auto position:', autoPos);
      node.pos = autoPos;
    }
    
    console.log('[AddNode] Final node position:', node.pos);

    // Update the canvas
    app.graph.setDirtyCanvas(true, true);

    console.log('[AddNode] Node added successfully with id:', node.id);

    return {
      success: true,
      data: {
        nodeId: node.id,
        nodeType: params.nodeType,
        position: node.pos as [number, number]
      }
    };
  } catch (error) {
    console.error('[AddNode] Error:', error);
    return {
      success: false,
      error: error instanceof Error ? error.message : String(error)
    };
  }
}
