export const normalizeEventSelector = (selector) => {
    if (typeof selector === "string") {
        const source = selector.split(".")[0];
        return { scope: source, event: selector };
    }
    return { scope: selector.scope, event: selector.event };
};
//# sourceMappingURL=events.js.map