import { createResourceContext, tap, withContextProvider, tapEffectEvent, } from "@assistant-ui/tap";
import { tapClientStack } from "./tap-client-stack-context.js";
const AssistantTapContext = createResourceContext(null);
export const withAssistantTapContextProvider = (value, fn) => {
    return withContextProvider(AssistantTapContext, value, fn);
};
const tapAssistantTapContext = () => {
    const ctx = tap(AssistantTapContext);
    if (!ctx)
        throw new Error("AssistantTapContext is not available");
    return ctx;
};
export const tapAssistantClientRef = () => {
    return tapAssistantTapContext().clientRef;
};
export const tapAssistantEmit = () => {
    const { emit } = tapAssistantTapContext();
    const clientStack = tapClientStack();
    return tapEffectEvent((event, payload) => {
        emit(event, payload, clientStack);
    });
};
//# sourceMappingURL=tap-assistant-context.js.map