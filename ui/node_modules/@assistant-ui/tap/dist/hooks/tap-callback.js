import { tapMemo } from "./tap-memo.js";
export const tapCallback = (fn, deps) => {
    // biome-ignore lint/correctness/useExhaustiveDependencies: user provided deps instead of callback identity
    return tapMemo(() => fn, deps);
};
//# sourceMappingURL=tap-callback.js.map