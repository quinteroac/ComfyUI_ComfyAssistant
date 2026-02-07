import type { AssistantClient, AssistantState } from "../types/client.js";
export declare const PROXIED_ASSISTANT_STATE_SYMBOL: unique symbol;
/**
 * Proxied state that lazily accesses scope states
 */
export declare const createProxiedAssistantState: (client: AssistantClient) => AssistantState;
export declare const getProxiedAssistantState: (client: AssistantClient) => AssistantState;
//# sourceMappingURL=proxied-assistant-state.d.ts.map