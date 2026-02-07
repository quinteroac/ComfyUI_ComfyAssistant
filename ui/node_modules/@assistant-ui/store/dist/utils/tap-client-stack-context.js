import { createResourceContext, tap, withContextProvider, tapMemo, } from "@assistant-ui/tap";
/**
 * Symbol used to get the client index from a ClientProxy.
 */
export const SYMBOL_CLIENT_INDEX = Symbol("assistant-ui.store.clientIndex");
/**
 * Get the index of a client (its position in the client stack when created).
 */
export const getClientIndex = (client) => {
    return client[SYMBOL_CLIENT_INDEX];
};
const ClientStackContext = createResourceContext([]);
/**
 * Get the current client stack inside a tap resource.
 */
export const tapClientStack = () => {
    return tap(ClientStackContext);
};
/**
 * Execute a callback with a client pushed onto the stack.
 * The stack is duplicated, not mutated.
 */
export const tapWithClientStack = (client, callback) => {
    const currentStack = tapClientStack();
    const newStack = tapMemo(() => [...currentStack, client], [currentStack, client]);
    return withContextProvider(ClientStackContext, newStack, callback);
};
//# sourceMappingURL=tap-client-stack-context.js.map