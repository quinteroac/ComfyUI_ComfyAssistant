import { ThreadAssistantMessagePart, ThreadUserMessagePart, MessagePartStatus, ToolCallMessagePartStatus } from "../../types/AssistantTypes.js";
import { ThreadRuntimeCoreBinding } from "./ThreadRuntime.js";
import type { MessageStateBinding } from "./RuntimeBindings.js";
import { SubscribableWithState } from "./subscribable/Subscribable.js";
import { Unsubscribe } from "../../types/index.js";
import { MessagePartRuntimePath } from "./RuntimePathTypes.js";
import { ToolResponse } from "assistant-stream";
export type MessagePartState = (ThreadUserMessagePart | ThreadAssistantMessagePart) & {
    readonly status: MessagePartStatus | ToolCallMessagePartStatus;
};
type MessagePartSnapshotBinding = SubscribableWithState<MessagePartState, MessagePartRuntimePath>;
export type MessagePartRuntime = {
    /**
     * Add tool result to a tool call message part that has no tool result yet.
     * This is useful when you are collecting a tool result via user input ("human tool calls").
     */
    addToolResult(result: any | ToolResponse<any>): void;
    /**
     * Resume a tool call that is waiting for human input with a payload.
     * This is useful when a tool has requested human input and is waiting for a response.
     */
    resumeToolCall(payload: unknown): void;
    readonly path: MessagePartRuntimePath;
    getState(): MessagePartState;
    subscribe(callback: () => void): Unsubscribe;
};
export declare class MessagePartRuntimeImpl implements MessagePartRuntime {
    private contentBinding;
    private messageApi?;
    private threadApi?;
    get path(): MessagePartRuntimePath;
    constructor(contentBinding: MessagePartSnapshotBinding, messageApi?: MessageStateBinding | undefined, threadApi?: ThreadRuntimeCoreBinding | undefined);
    protected __internal_bindMethods(): void;
    getState(): MessagePartState;
    addToolResult(result: any | ToolResponse<any>): void;
    resumeToolCall(payload: unknown): void;
    subscribe(callback: () => void): Unsubscribe;
}
export {};
//# sourceMappingURL=MessagePartRuntime.d.ts.map