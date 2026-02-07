import { ThreadMessageLike } from "./ThreadMessageLike.js";
import { ThreadMessage } from "../../../types/index.js";
import { ToolExecutionStatus } from "../assistant-transport/useToolInvocations.js";
import { ReadonlyJSONValue } from "assistant-stream/utils";
export declare namespace useExternalMessageConverter {
    type Message = (ThreadMessageLike & {
        readonly convertConfig?: {
            readonly joinStrategy?: "concat-content" | "none";
        };
    }) | {
        role: "tool";
        toolCallId: string;
        toolName?: string | undefined;
        result: any;
        artifact?: any;
        isError?: boolean;
        messages?: readonly ThreadMessage[];
    };
    type Metadata = {
        readonly toolStatuses?: Record<string, ToolExecutionStatus>;
        readonly error?: ReadonlyJSONValue;
    };
    type Callback<T> = (message: T, metadata: Metadata) => Message | Message[];
}
export declare const convertExternalMessages: <T extends WeakKey>(messages: T[], callback: useExternalMessageConverter.Callback<T>, isRunning: boolean, metadata: useExternalMessageConverter.Metadata) => ThreadMessage[];
export declare const useExternalMessageConverter: <T extends WeakKey>({ callback, messages, isRunning, joinStrategy, metadata, }: {
    callback: useExternalMessageConverter.Callback<T>;
    messages: T[];
    isRunning: boolean;
    joinStrategy?: "concat-content" | "none" | undefined;
    metadata?: useExternalMessageConverter.Metadata | undefined;
}) => ThreadMessage[];
//# sourceMappingURL=external-message-converter.d.ts.map