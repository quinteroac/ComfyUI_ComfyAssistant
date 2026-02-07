/**
 * Creates hooks for accessing a store within a context.
 * @param contextHook - The hook to access the context.
 * @param contextKey - The key of the store in the context.
 * @returns An object containing the hooks: `use...` and `use...Store`.
 */
export function createContextStoreHook(contextHook, contextKey) {
    function useStoreStoreHook(options) {
        const context = contextHook(options);
        if (!context)
            return null;
        return context[contextKey];
    }
    function useStoreHook(param) {
        let optional = false;
        let selector;
        if (typeof param === "function") {
            selector = param;
        }
        else if (param && typeof param === "object") {
            optional = !!param.optional;
            selector = param.selector;
        }
        const store = useStoreStoreHook({
            optional,
        });
        if (!store)
            return null;
        return selector ? store(selector) : store();
    }
    // Return an object with keys based on contextKey
    return {
        [contextKey]: useStoreHook,
        [`${contextKey}Store`]: useStoreStoreHook,
    };
}
//# sourceMappingURL=createContextStoreHook.js.map