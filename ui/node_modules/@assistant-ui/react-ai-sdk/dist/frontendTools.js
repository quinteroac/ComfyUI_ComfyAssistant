import { jsonSchema } from "ai";
export const frontendTools = (tools) => Object.fromEntries(Object.entries(tools).map(([name, tool]) => [
    name,
    {
        ...(tool.description ? { description: tool.description } : undefined),
        inputSchema: jsonSchema(tool.parameters),
    },
]));
//# sourceMappingURL=frontendTools.js.map