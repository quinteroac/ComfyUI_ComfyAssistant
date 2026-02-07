import { SpeechState, SubmittedFeedback } from "../runtime-cores/core/ThreadRuntimeCore.js";
import { ThreadMessage, ThreadAssistantMessagePart, ThreadUserMessagePart, Unsubscribe } from "../../types/index.js";
import { RunConfig, ToolCallMessagePartStatus } from "../../types/AssistantTypes.js";
import { AttachmentRuntime, MessageAttachmentRuntimeImpl } from "./AttachmentRuntime.js";
import { EditComposerRuntime, EditComposerRuntimeImpl } from "./ComposerRuntime.js";
import { MessagePartRuntime, MessagePartRuntimeImpl } from "./MessagePartRuntime.js";
import { MessageRuntimePath } from "./RuntimePathTypes.js";
import { ThreadRuntimeCoreBinding } from "./ThreadRuntime.js";
import type { MessageStateBinding } from "./RuntimeBindings.js";
export declare const toMessagePartStatus: (message: ThreadMessage, partIndex: number, part: ThreadUserMessagePart | ThreadAssistantMessagePart) => ToolCallMessagePartStatus;
export type MessageState = ThreadMessage & {
    readonly parentId: string | null;
    /** The position of this message in the thread (0 for first message) */
    readonly index: number;
    readonly isLast: boolean;
    readonly branchNumber: number;
    readonly branchCount: number;
    /**
     * @deprecated This API is still under active development and might change without notice.
     */
    readonly speech: SpeechState | undefined;
    /**
     * @deprecated Use `message.metadata.submittedFeedback` instead. This will be removed in 0.12.0.
     */
    readonly submittedFeedback: SubmittedFeedback | undefined;
};
export type { MessageStateBinding } from "./RuntimeBindings.js";
type ReloadConfig = {
    runConfig?: RunConfig;
};
export type MessageRuntime = {
    readonly path: MessageRuntimePath;
    readonly composer: EditComposerRuntime;
    getState(): MessageState;
    reload(config?: ReloadConfig): void;
    /**
     * @deprecated This API is still under active development and might change without notice.
     */
    speak(): void;
    /**
     * @deprecated This API is still under active development and might change without notice.
     */
    stopSpeaking(): void;
    submitFeedback({ type }: {
        type: "positive" | "negative";
    }): void;
    switchToBranch({ position, branchId, }: {
        position?: "previous" | "next" | undefined;
        branchId?: string | undefined;
    }): void;
    unstable_getCopyText(): string;
    subscribe(callback: () => void): Unsubscribe;
    getMessagePartByIndex(idx: number): MessagePartRuntime;
    getMessagePartByToolCallId(toolCallId: string): MessagePartRuntime;
    getAttachmentByIndex(idx: number): AttachmentRuntime & {
        source: "message";
    };
};
export declare class MessageRuntimeImpl implements MessageRuntime {
    private _core;
    private _threadBinding;
    get path(): MessageRuntimePath;
    constructor(_core: MessageStateBinding, _threadBinding: ThreadRuntimeCoreBinding);
    protected __internal_bindMethods(): void;
    readonly composer: EditComposerRuntimeImpl;
    private _getEditComposerRuntimeCore;
    getState(): ThreadMessage & {
        readonly parentId: string | null;
        readonly index: number;
        readonly isLast: boolean;
        readonly branchNumber: number;
        readonly branchCount: number;
        readonly speech: SpeechState | undefined;
        readonly submittedFeedback: SubmittedFeedback | undefined;
    };
    reload(reloadConfig?: ReloadConfig): void;
    speak(): void;
    stopSpeaking(): void;
    submitFeedback({ type }: {
        type: "positive" | "negative";
    }): void;
    switchToBranch({ position, branchId, }: {
        position?: "previous" | "next" | undefined;
        branchId?: string | undefined;
    }): void;
    unstable_getCopyText(): string;
    subscribe(callback: () => void): Unsubscribe;
    getMessagePartByIndex(idx: number): MessagePartRuntimeImpl;
    getMessagePartByToolCallId(toolCallId: string): MessagePartRuntimeImpl;
    getAttachmentByIndex(idx: number): MessageAttachmentRuntimeImpl;
}
//# sourceMappingURL=MessageRuntime.d.ts.map