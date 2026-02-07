import { type Tool } from "assistant-stream";
import type { AssistantTransportCommand, AssistantTransportState } from "./types.js";
type UseToolInvocationsParams = {
    state: AssistantTransportState;
    getTools: () => Record<string, Tool> | undefined;
    onResult: (command: AssistantTransportCommand) => void;
    setToolStatuses: (updater: Record<string, ToolExecutionStatus> | ((prev: Record<string, ToolExecutionStatus>) => Record<string, ToolExecutionStatus>)) => void;
};
export type ToolExecutionStatus = {
    type: "executing";
} | {
    type: "interrupt";
    payload: {
        type: "human";
        payload: unknown;
    };
};
export declare function useToolInvocations({ state, getTools, onResult, setToolStatuses, }: UseToolInvocationsParams): {
    reset: () => void;
    abort: () => Promise<void>;
    resume: (toolCallId: string, payload: unknown) => void;
};
export {};
//# sourceMappingURL=useToolInvocations.d.ts.map