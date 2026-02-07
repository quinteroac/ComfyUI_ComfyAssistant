import { type UIMessage } from "@ai-sdk/react";
import type { AssistantCloud } from "assistant-cloud";
import { AssistantRuntime } from "@assistant-ui/react";
import { type AISDKRuntimeAdapter, type CustomToCreateMessageFunction } from "./useAISDKRuntime.js";
import { ChatInit } from "ai";
export type UseChatRuntimeOptions<UI_MESSAGE extends UIMessage = UIMessage> = ChatInit<UI_MESSAGE> & {
    cloud?: AssistantCloud | undefined;
    adapters?: AISDKRuntimeAdapter["adapters"] | undefined;
    toCreateMessage?: CustomToCreateMessageFunction;
};
export declare const useChatRuntime: <UI_MESSAGE extends UIMessage = UIMessage>({ cloud, ...options }?: UseChatRuntimeOptions<UI_MESSAGE>) => AssistantRuntime;
//# sourceMappingURL=useChatRuntime.d.ts.map