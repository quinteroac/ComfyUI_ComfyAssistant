"use client";
import { createActionButton, } from "../../utils/createActionButton.js";
import { useCallback } from "react";
import { useThreadViewport, useThreadViewportStore, } from "../../context/react/ThreadViewportContext.js";
const useThreadScrollToBottom = ({ behavior, } = {}) => {
    const isAtBottom = useThreadViewport((s) => s.isAtBottom);
    const threadViewportStore = useThreadViewportStore();
    const handleScrollToBottom = useCallback(() => {
        threadViewportStore.getState().scrollToBottom({ behavior });
    }, [threadViewportStore, behavior]);
    if (isAtBottom)
        return null;
    return handleScrollToBottom;
};
export const ThreadPrimitiveScrollToBottom = createActionButton("ThreadPrimitive.ScrollToBottom", useThreadScrollToBottom, ["behavior"]);
//# sourceMappingURL=ThreadScrollToBottom.js.map