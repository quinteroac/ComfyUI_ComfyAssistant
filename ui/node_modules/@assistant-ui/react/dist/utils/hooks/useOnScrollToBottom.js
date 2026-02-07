"use client";
import { useCallbackRef } from "@radix-ui/react-use-callback-ref";
import { useEffect } from "react";
import { useThreadViewport } from "../../context/react/ThreadViewportContext.js";
export const useOnScrollToBottom = (callback) => {
    const callbackRef = useCallbackRef(callback);
    const onScrollToBottom = useThreadViewport((vp) => vp.onScrollToBottom);
    useEffect(() => {
        return onScrollToBottom(callbackRef);
    }, [onScrollToBottom, callbackRef]);
};
//# sourceMappingURL=useOnScrollToBottom.js.map