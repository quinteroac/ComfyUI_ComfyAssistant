import type { ToolCallMessagePartComponent } from "../types/MessagePartComponentTypes.js";
export type AssistantToolUIProps<TArgs, TResult> = {
    toolName: string;
    render: ToolCallMessagePartComponent<TArgs, TResult>;
};
export declare const useAssistantToolUI: (tool: AssistantToolUIProps<any, any> | null) => void;
//# sourceMappingURL=useAssistantToolUI.d.ts.map