"use client";
import { useAssistantToolUI, } from "./useAssistantToolUI.js";
export const makeAssistantToolUI = (tool) => {
    const ToolUI = () => {
        useAssistantToolUI(tool);
        return null;
    };
    ToolUI.unstable_tool = tool;
    return ToolUI;
};
//# sourceMappingURL=makeAssistantToolUI.js.map