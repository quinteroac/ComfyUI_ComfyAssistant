import { z } from "zod";

export const searchTemplatesSchema = z.object({
  query: z.string().optional().describe("Term to search for in template titles, descriptions, or categories (e.g., 'wan', 'flux', 'i2v')."),
  category: z.string().optional().describe("Optional filter by category (e.g., 'video', 'image', 'generation')."),
});

export type SearchTemplatesArgs = z.infer<typeof searchTemplatesSchema>;
