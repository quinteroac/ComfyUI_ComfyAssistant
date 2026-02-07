/**
 * Wrapper and helpers to facilitate access to the ComfyUI API
 */

import type { ComfyApp } from '@comfyorg/comfyui-frontend-types';

/**
 * Helper class to interact with the ComfyUI API more easily
 */
export class ComfyAPI {
  constructor(private app: ComfyApp) {}

  /**
   * Adds a node to the workflow
   */
  addNode(type: string, position?: { x: number; y: number }) {
    // Use LiteGraph.createNode to create the node first (correct ComfyUI pattern)
    const LiteGraph = (window as any).LiteGraph;
    if (!LiteGraph) {
      console.error('LiteGraph is not available');
      return null;
    }
    
    const node = LiteGraph.createNode(type);
    if (!node) {
      console.error(`Could not create node of type: ${type}`);
      return null;
    }
    
    if (position) {
      node.pos = [position.x, position.y];
    }
    
    this.app.graph.add(node);
    this.app.graph.setDirtyCanvas(true, true);
    return node;
  }

  /**
   * Removes a node by ID
   */
  removeNode(nodeId: string | number) {
    const node = this.app.graph.getNodeById(nodeId);
    if (node) {
      this.app.graph.remove(node);
      this.app.graph.setDirtyCanvas(true, true);
      return true;
    }
    return false;
  }

  /**
   * Connects two nodes
   */
  connectNodes(
    sourceNodeId: string | number,
    sourceSlot: number,
    targetNodeId: string | number,
    targetSlot: number
  ) {
    const sourceNode = this.app.graph.getNodeById(sourceNodeId);
    const targetNode = this.app.graph.getNodeById(targetNodeId);
    
    if (!sourceNode || !targetNode) {
      return null;
    }

    const linkId = sourceNode.connect(sourceSlot, targetNode, targetSlot);
    this.app.graph.setDirtyCanvas(true, true);
    return linkId;
  }

  /**
   * Gets all nodes in the workflow
   */
  getNodes() {
    return this.app.graph._nodes;
  }

  /**
   * Gets a node by ID
   */
  getNodeById(nodeId: string | number) {
    return this.app.graph.getNodeById(nodeId);
  }

  /**
   * Gets all available node types
   */
  getAvailableNodeTypes() {
    return Object.keys((this.app.ui as any).nodeTemplates || {});
  }

  /**
   * Clears the entire workflow
   */
  clearWorkflow() {
    this.app.graph.clear();
    this.app.graph.setDirtyCanvas(true, true);
  }
}

/**
 * Helper to check if the ComfyUI app is available
 */
export function isComfyAppAvailable(): boolean {
  return typeof window !== 'undefined' && window.app !== undefined;
}

/**
 * Helper to safely get the ComfyAPI instance
 */
export function getComfyAPI(): ComfyAPI | null {
  if (isComfyAppAvailable() && window.app) {
    return new ComfyAPI(window.app);
  }
  return null;
}
