import type { JSONSchema7 } from "json-schema";
import { zodToJsonSchema } from "zod-to-json-schema";
import { searchTemplatesSchema } from "./searchTemplates";
import { applyTemplateSchema } from "./applyTemplate";

// Existing definitions (I will append the new ones)
export * from "./add-node";
export * from "./remove-node";
export * from "./connect-nodes";
export * from "./get-workflow-info";
export * from "./set-node-widget-value";
export * from "./fill-prompt-node";
export * from "./create-skill";
export * from "./delete-skill";
export * from "./update-skill";
export * from "./get-user-skill";
export * from "./list-user-skills";
export * from "./list-system-skills";
export * from "./get-system-skill";
export * from "./refresh-environment";
export * from "./search-installed-nodes";
export * from "./read-documentation";
export * from "./get-available-models";
export * from "./execute-workflow";
export * from "./apply-workflow-json";
export * from "./get-example-workflow";
export * from "./web-search";
export * from "./fetch-web-content";
export * from "./search-node-registry";

export const searchTemplatesDefinition = {
  name: "searchTemplates",
  description: "Searches for official and community workflow templates by title, description, or category (e.g., 'wan', 'flux'). Use this to find a starting point for complex workflows.",
  parameters: zodToJsonSchema(searchTemplatesSchema) as JSONSchema7,
};

export const applyTemplateDefinition = {
  name: "applyTemplate",
  description: "Downloads and applies a selected workflow template to the canvas. Replaces the current graph.",
  parameters: zodToJsonSchema(applyTemplateSchema) as JSONSchema7,
};
