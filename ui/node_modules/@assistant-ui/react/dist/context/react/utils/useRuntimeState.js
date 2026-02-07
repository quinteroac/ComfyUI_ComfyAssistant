import { useDebugValue, useSyncExternalStore } from "react";
import { ensureBinding } from "./ensureBinding.js";
export function useRuntimeStateInternal(runtime, selector = identity) {
    // TODO move to useRuntimeState
    ensureBinding(runtime);
    const slice = useSyncExternalStore(runtime.subscribe, () => selector(runtime.getState()), () => selector(runtime.getState()));
    useDebugValue(slice);
    return slice;
}
const identity = (arg) => arg;
export function useRuntimeState(runtime, selector) {
    // ensure that the runtime is bound
    // ensureBinding(runtime);
    return useRuntimeStateInternal(runtime, selector);
}
//# sourceMappingURL=useRuntimeState.js.map