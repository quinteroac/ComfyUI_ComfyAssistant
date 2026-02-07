import { useState, useCallback, useRef, useEffect } from "react";
export const createInitialQueueState = () => ({
    queued: [],
    inTransit: [],
});
export const useCommandQueue = (opts) => {
    const onQueueRef = useRef(opts.onQueue);
    useEffect(() => {
        onQueueRef.current = opts.onQueue;
    });
    const [, rerender] = useState(0);
    const queueStateRef = useRef(createInitialQueueState());
    const enqueue = (command) => {
        queueStateRef.current = {
            queued: [...queueStateRef.current.queued, command],
            inTransit: queueStateRef.current.inTransit,
        };
        rerender((prev) => prev + 1);
        onQueueRef.current();
    };
    const flush = () => {
        if (queueStateRef.current.queued.length === 0)
            return [];
        const queued = queueStateRef.current.queued;
        queueStateRef.current = {
            queued: [],
            inTransit: [...queueStateRef.current.inTransit, ...queued],
        };
        rerender((prev) => prev + 1);
        return queued;
    };
    const markDelivered = () => {
        queueStateRef.current = { ...queueStateRef.current, inTransit: [] };
        rerender((prev) => prev + 1);
    };
    const reset = useCallback(() => {
        queueStateRef.current = createInitialQueueState();
        rerender((prev) => prev + 1);
    }, []);
    return {
        state: queueStateRef.current,
        enqueue,
        flush,
        markDelivered,
        reset,
    };
};
//# sourceMappingURL=commandQueue.js.map