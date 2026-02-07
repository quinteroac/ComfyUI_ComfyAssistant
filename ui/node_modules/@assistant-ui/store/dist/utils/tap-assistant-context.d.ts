import type { AssistantEventName, AssistantEventPayload } from "../types/events.js";
import type { AssistantClient } from "../types/client.js";
import { type ClientStack } from "./tap-client-stack-context.js";
type EmitFn = <TEvent extends Exclude<AssistantEventName, "*">>(event: TEvent, payload: AssistantEventPayload[TEvent], clientStack: ClientStack) => void;
export type AssistantTapContextValue = {
    clientRef: {
        parent: AssistantClient;
        current: AssistantClient | null;
    };
    emit: EmitFn;
};
export declare const withAssistantTapContextProvider: <TResult>(value: AssistantTapContextValue, fn: () => TResult) => TResult;
export declare const tapAssistantClientRef: () => {
    parent: AssistantClient;
    current: AssistantClient | null;
};
export declare const tapAssistantEmit: () => <TEvent extends Exclude<AssistantEventName, "*">>(event: TEvent, payload: AssistantEventPayload[TEvent]) => void;
export {};
//# sourceMappingURL=tap-assistant-context.d.ts.map