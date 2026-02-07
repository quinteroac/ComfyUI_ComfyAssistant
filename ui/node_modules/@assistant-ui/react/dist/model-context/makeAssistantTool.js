"use client";
import { useAssistantTool } from "./useAssistantTool.js";
export const makeAssistantTool = (tool) => {
    const Tool = () => {
        useAssistantTool(tool);
        return null;
    };
    Tool.unstable_tool = tool;
    return Tool;
};
//# sourceMappingURL=makeAssistantTool.js.map