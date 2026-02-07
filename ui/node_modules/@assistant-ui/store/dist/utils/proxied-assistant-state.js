"use client";
import { getClientState } from "../tapClientResource.js";
import { BaseProxyHandler, handleIntrospectionProp } from "./BaseProxyHandler.js";
export const PROXIED_ASSISTANT_STATE_SYMBOL = Symbol("assistant-ui.store.proxiedAssistantState");
const isIgnoredKey = (key) => {
    return key === "on" || key === "subscribe" || typeof key === "symbol";
};
/**
 * Proxied state that lazily accesses scope states
 */
export const createProxiedAssistantState = (client) => {
    class ProxiedAssistantStateProxyHandler extends BaseProxyHandler {
        get(_, prop) {
            const introspection = handleIntrospectionProp(prop, "AssistantState");
            if (introspection !== false)
                return introspection;
            const scope = prop;
            if (isIgnoredKey(scope))
                return undefined;
            return getClientState(client[scope]());
        }
        ownKeys() {
            return Object.keys(client).filter((key) => !isIgnoredKey(key));
        }
        has(_, prop) {
            return !isIgnoredKey(prop) && prop in client;
        }
    }
    return new Proxy({}, new ProxiedAssistantStateProxyHandler());
};
export const getProxiedAssistantState = (client) => {
    return client[PROXIED_ASSISTANT_STATE_SYMBOL];
};
//# sourceMappingURL=proxied-assistant-state.js.map