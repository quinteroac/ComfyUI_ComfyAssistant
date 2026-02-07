import { tapState } from "./tap-state.js";
export function tapRef(initialValue) {
    const [state] = tapState(() => ({
        current: initialValue,
    }));
    return state;
}
//# sourceMappingURL=tap-ref.js.map