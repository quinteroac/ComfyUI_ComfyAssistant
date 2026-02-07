import { FC } from "react";
import { type AssistantToolUIProps } from "./useAssistantToolUI.js";
export type AssistantToolUI = FC & {
    unstable_tool: AssistantToolUIProps<any, any>;
};
export declare const makeAssistantToolUI: <TArgs, TResult>(tool: AssistantToolUIProps<TArgs, TResult>) => AssistantToolUI;
//# sourceMappingURL=makeAssistantToolUI.d.ts.map