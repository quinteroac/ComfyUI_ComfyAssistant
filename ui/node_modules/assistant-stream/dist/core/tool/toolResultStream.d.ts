import { Tool } from "./tool-types.js";
import { ToolExecutionStream } from "./ToolExecutionStream.js";
import { AssistantMessage } from "../utils/types.js";
export declare function unstable_runPendingTools(message: AssistantMessage, tools: Record<string, Tool> | undefined, abortSignal: AbortSignal, human: (toolCallId: string, payload: unknown) => Promise<unknown>): Promise<AssistantMessage>;
export type ToolResultStreamOptions = {
    onExecutionStart?: (toolCallId: string, toolName: string) => void;
    onExecutionEnd?: (toolCallId: string, toolName: string) => void;
};
export declare function toolResultStream(tools: Record<string, Tool> | (() => Record<string, Tool> | undefined) | undefined, abortSignal: AbortSignal | (() => AbortSignal), human: (toolCallId: string, payload: unknown) => Promise<unknown>, options?: ToolResultStreamOptions): ToolExecutionStream;
//# sourceMappingURL=toolResultStream.d.ts.map