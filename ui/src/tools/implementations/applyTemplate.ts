import { ApplyTemplateArgs } from "../definitions/applyTemplate";
import { executeApplyWorkflowJson } from "./apply-workflow-json";
import { ToolContext } from "../types";

export const applyTemplate = async (params: ApplyTemplateArgs, context: ToolContext) => {
  const { id, source, package: pkg } = params;
  let url = "";

  if (source === "official") {
    url = `/templates/${id}.json`;
  } else {
    if (!pkg) {
      throw new Error("Package name is required for custom source templates.");
    }
    url = `/api/workflow_templates/${pkg}/${id}`;
  }

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch template from ${url}: ${response.statusText}`);
    }

    const workflow = await response.json();
    
    // Check if the workflow is in the expected API format (object with node IDs)
    // or if it's wrapped in a 'prompt' property
    const actualWorkflow = workflow.prompt || workflow;

    // Use the existing applyWorkflowJson implementation to load it
    return await executeApplyWorkflowJson({ workflow: actualWorkflow }, context);
  } catch (error) {
    console.error("Error applying template:", error);
    throw new Error("Failed to apply template: " + (error as Error).message);
  }
};
