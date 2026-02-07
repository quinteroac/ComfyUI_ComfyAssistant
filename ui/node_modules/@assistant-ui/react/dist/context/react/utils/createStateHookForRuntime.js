import { useRuntimeStateInternal, } from "./useRuntimeState.js";
export function createStateHookForRuntime(useRuntime) {
    function useStoreHook(param) {
        let optional = false;
        let selector;
        if (typeof param === "function") {
            selector = param;
        }
        else if (param) {
            optional = !!param.optional;
            selector = param.selector;
        }
        const store = useRuntime({ optional });
        if (!store)
            return null;
        // it is ok to call useRuntimeStateInternal conditionally because it will never become null if its available
        return useRuntimeStateInternal(store, selector);
    }
    return useStoreHook;
}
//# sourceMappingURL=createStateHookForRuntime.js.map