import type { UIMessage, useChat, CreateUIMessage } from "@ai-sdk/react";
import { type ExternalStoreAdapter, type ThreadHistoryAdapter, type AssistantRuntime, type AppendMessage } from "@assistant-ui/react";
export type CustomToCreateMessageFunction = <UI_MESSAGE extends UIMessage = UIMessage>(message: AppendMessage) => CreateUIMessage<UI_MESSAGE>;
export type AISDKRuntimeAdapter = {
    adapters?: (NonNullable<ExternalStoreAdapter["adapters"]> & {
        history?: ThreadHistoryAdapter | undefined;
    }) | undefined;
    toCreateMessage?: CustomToCreateMessageFunction;
    /**
     * Whether to automatically cancel pending interactive tool calls when the user sends a new message.
     *
     * When enabled (default), the pending tool calls will be marked as failed with an error message
     * indicating the user cancelled the tool call by sending a new message.
     *
     * @default true
     */
    cancelPendingToolCallsOnSend?: boolean | undefined;
};
export declare const useAISDKRuntime: <UI_MESSAGE extends UIMessage = UIMessage>(chatHelpers: ReturnType<typeof useChat<UI_MESSAGE>>, { adapters, toCreateMessage: customToCreateMessage, cancelPendingToolCallsOnSend, }?: AISDKRuntimeAdapter) => AssistantRuntime;
//# sourceMappingURL=useAISDKRuntime.d.ts.map