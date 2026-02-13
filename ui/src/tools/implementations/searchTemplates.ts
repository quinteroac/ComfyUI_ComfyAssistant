import { SearchTemplatesArgs } from "../definitions/searchTemplates";

export const searchTemplates = async ({ query, category }: SearchTemplatesArgs) => {
  const results: any[] = [];
  const q = query?.toLowerCase() || "";

  try {
    // 1. Fetch Official Templates
    const officialResponse = await fetch("/templates/index.json");
    if (officialResponse.ok) {
      const officialData = await officialResponse.json();
      // officialData is an array of categories/modules
      for (const module of officialData) {
        if (category && module.type !== category && module.title?.toLowerCase() !== category.toLowerCase()) continue;
        
        for (const template of module.templates || []) {
          const matchQuery = !q || 
            template.title?.toLowerCase().includes(q) || 
            template.description?.toLowerCase().includes(q) ||
            template.name?.toLowerCase().includes(q);
            
          if (matchQuery) {
            results.push({
              id: template.name,
              title: template.title,
              description: template.description,
              source: "official",
              category: module.title || module.type,
              models: template.models || []
            });
          }
        }
      }
    }

    // 2. Fetch Custom Node Templates
    const customResponse = await fetch("/api/workflow_templates");
    if (customResponse.ok) {
      const customData = await customResponse.json();
      // customData is { "package-name": ["template1.json", ...] }
      for (const [pkg, templates] of Object.entries(customData)) {
        for (const templateFile of (templates as string[])) {
          const matchQuery = !q || 
            pkg.toLowerCase().includes(q) || 
            templateFile.toLowerCase().includes(q);
            
          if (matchQuery) {
            results.push({
              id: templateFile,
              title: templateFile.replace(".json", "").replace(/_/g, " ").replace(/-/g, " "),
              description: `Template provided by ${pkg}`,
              source: "custom",
              package: pkg,
              category: "Community"
            });
          }
        }
      }
    }

    return { 
      templates: results.slice(0, 20), // Limit to top 20 for context efficiency
      total: results.length 
    };
  } catch (error) {
    console.error("Error searching templates:", error);
    throw new Error("Failed to search templates: " + (error as Error).message);
  }
};
