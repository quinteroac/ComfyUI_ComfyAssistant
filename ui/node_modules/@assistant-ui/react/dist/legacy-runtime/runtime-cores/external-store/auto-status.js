const symbolAutoStatus = Symbol("autoStatus");
const AUTO_STATUS_RUNNING = Object.freeze(Object.assign({ type: "running" }, { [symbolAutoStatus]: true }));
const AUTO_STATUS_COMPLETE = Object.freeze(Object.assign({
    type: "complete",
    reason: "unknown",
}, { [symbolAutoStatus]: true }));
const AUTO_STATUS_PENDING = Object.freeze(Object.assign({
    type: "requires-action",
    reason: "tool-calls",
}, { [symbolAutoStatus]: true }));
const AUTO_STATUS_INTERRUPT = Object.freeze(Object.assign({
    type: "requires-action",
    reason: "interrupt",
}, { [symbolAutoStatus]: true }));
export const isAutoStatus = (status) => status[symbolAutoStatus] === true;
export const getAutoStatus = (isLast, isRunning, hasInterruptedToolCalls, hasPendingToolCalls, error) => {
    if (isLast && error) {
        return Object.assign({
            type: "incomplete",
            reason: "error",
            error: error,
        }, { [symbolAutoStatus]: true });
    }
    return isLast && isRunning
        ? AUTO_STATUS_RUNNING
        : hasInterruptedToolCalls
            ? AUTO_STATUS_INTERRUPT
            : hasPendingToolCalls
                ? AUTO_STATUS_PENDING
                : AUTO_STATUS_COMPLETE;
};
//# sourceMappingURL=auto-status.js.map