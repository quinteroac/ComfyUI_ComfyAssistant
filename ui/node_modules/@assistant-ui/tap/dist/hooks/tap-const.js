import { tapState } from "./tap-state.js";
export function tapConst(getValue, _deps) {
    const [state] = tapState(getValue);
    return state;
}
//# sourceMappingURL=tap-const.js.map