import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext } from "react";
import { createProxiedAssistantState, PROXIED_ASSISTANT_STATE_SYMBOL, } from "./proxied-assistant-state.js";
import { BaseProxyHandler, handleIntrospectionProp } from "./BaseProxyHandler.js";
const NO_OP_SUBSCRIBE = () => () => { };
const createErrorClientField = (message) => {
    const fn = (() => {
        throw new Error(message);
    });
    fn.source = null;
    fn.query = null;
    return fn;
};
class DefaultAssistantClientProxyHandler extends BaseProxyHandler {
    get(_, prop) {
        if (prop === "subscribe")
            return NO_OP_SUBSCRIBE;
        if (prop === "on")
            return NO_OP_SUBSCRIBE;
        if (prop === PROXIED_ASSISTANT_STATE_SYMBOL)
            return DefaultAssistantClientProxiedAssistantState;
        const introspection = handleIntrospectionProp(prop, "DefaultAssistantClient");
        if (introspection !== false)
            return introspection;
        return createErrorClientField("You are using a component or hook that requires an AuiProvider. Wrap your component in an <AuiProvider> component.");
    }
    ownKeys() {
        return ["subscribe", "on", PROXIED_ASSISTANT_STATE_SYMBOL];
    }
    has(_, prop) {
        return (prop === "subscribe" ||
            prop === "on" ||
            prop === PROXIED_ASSISTANT_STATE_SYMBOL);
    }
}
/** Default context value - throws "wrap in AuiProvider" error */
export const DefaultAssistantClient = new Proxy({}, new DefaultAssistantClientProxyHandler());
const DefaultAssistantClientProxiedAssistantState = createProxiedAssistantState(DefaultAssistantClient);
/** Root prototype for created clients - throws "scope not defined" error */
export const createRootAssistantClient = () => new Proxy({}, {
    get(_, prop) {
        const introspection = handleIntrospectionProp(prop, "AssistantClient");
        if (introspection !== false)
            return introspection;
        return createErrorClientField(`The current scope does not have a "${String(prop)}" property.`);
    },
});
/**
 * React Context for the AssistantClient
 */
const AssistantContext = createContext(DefaultAssistantClient);
export const useAssistantContextValue = () => {
    return useContext(AssistantContext);
};
/**
 * Provider component for AssistantClient
 *
 * @example
 * ```typescript
 * <AuiProvider value={aui}>
 *   <YourApp />
 * </AuiProvider>
 * ```
 */
export const AuiProvider = ({ value, children, }) => {
    return (_jsx(AssistantContext.Provider, { value: value, children: children }));
};
//# sourceMappingURL=react-assistant-context.js.map