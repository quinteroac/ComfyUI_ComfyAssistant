import { z } from "zod";

export const applyTemplateSchema = z.object({
  id: z.string().describe("The unique identifier or filename of the template."),
  source: z.enum(["official", "custom"]).describe("The source of the template: 'official' (from /templates) or 'custom' (from /api/workflow_templates)."),
  package: z.string().optional().describe("For 'custom' source, the name of the custom node package that provides the template."),
});

export type ApplyTemplateArgs = z.infer<typeof applyTemplateSchema>;
