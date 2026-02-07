"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { useComposedRefs } from "@radix-ui/react-compose-refs";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef, useCallback, } from "react";
import { useThreadViewportAutoScroll } from "./useThreadViewportAutoScroll.js";
import { ThreadPrimitiveViewportProvider } from "../../context/providers/ThreadViewportProvider.js";
import { useSizeHandle } from "../../utils/hooks/useSizeHandle.js";
import { useThreadViewport } from "../../context/react/ThreadViewportContext.js";
const useViewportSizeRef = () => {
    const register = useThreadViewport((s) => s.registerViewport);
    const getHeight = useCallback((el) => el.clientHeight, []);
    return useSizeHandle(register, getHeight);
};
const ThreadPrimitiveViewportScrollable = forwardRef(({ autoScroll, scrollToBottomOnRunStart, scrollToBottomOnInitialize, scrollToBottomOnThreadSwitch, children, ...rest }, forwardedRef) => {
    const autoScrollRef = useThreadViewportAutoScroll({
        autoScroll,
        scrollToBottomOnRunStart,
        scrollToBottomOnInitialize,
        scrollToBottomOnThreadSwitch,
    });
    const viewportSizeRef = useViewportSizeRef();
    const ref = useComposedRefs(forwardedRef, autoScrollRef, viewportSizeRef);
    return (_jsx(Primitive.div, { ...rest, ref: ref, children: children }));
});
ThreadPrimitiveViewportScrollable.displayName =
    "ThreadPrimitive.ViewportScrollable";
/**
 * A scrollable viewport container for thread messages.
 *
 * This component provides a scrollable area for displaying thread messages with
 * automatic scrolling capabilities. It manages the viewport state and provides
 * context for child components to access viewport-related functionality.
 *
 * @example
 * ```tsx
 * <ThreadPrimitive.Viewport turnAnchor="top">
 *   <ThreadPrimitive.Messages components={{ Message: MyMessage }} />
 * </ThreadPrimitive.Viewport>
 * ```
 */
export const ThreadPrimitiveViewport = forwardRef(({ turnAnchor, ...props }, ref) => {
    return (_jsx(ThreadPrimitiveViewportProvider, { options: { turnAnchor }, children: _jsx(ThreadPrimitiveViewportScrollable, { ...props, ref: ref }) }));
});
ThreadPrimitiveViewport.displayName = "ThreadPrimitive.Viewport";
//# sourceMappingURL=ThreadViewport.js.map