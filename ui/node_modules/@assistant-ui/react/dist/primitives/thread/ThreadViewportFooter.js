"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { useComposedRefs } from "@radix-ui/react-compose-refs";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef, useCallback, } from "react";
import { useSizeHandle } from "../../utils/hooks/useSizeHandle.js";
import { useThreadViewport } from "../../context/react/ThreadViewportContext.js";
/**
 * A footer container that measures its height for scroll calculations.
 *
 * This component measures its height and provides it to the viewport context
 * for use in scroll calculations (e.g., ViewportSlack min-height).
 *
 * Multiple ViewportFooter components can be used - their heights are summed.
 *
 * Typically used with `className="sticky bottom-0"` to keep the footer
 * visible at the bottom of the viewport while scrolling.
 *
 * @example
 * ```tsx
 * <ThreadPrimitive.Viewport>
 *   <ThreadPrimitive.Messages components={{ ... }} />
 *   <ThreadPrimitive.ViewportFooter className="sticky bottom-0">
 *     <Composer />
 *   </ThreadPrimitive.ViewportFooter>
 * </ThreadPrimitive.Viewport>
 * ```
 */
export const ThreadPrimitiveViewportFooter = forwardRef((props, forwardedRef) => {
    const register = useThreadViewport((s) => s.registerContentInset);
    const getHeight = useCallback((el) => {
        const marginTop = parseFloat(getComputedStyle(el).marginTop) || 0;
        return el.offsetHeight + marginTop;
    }, []);
    const resizeRef = useSizeHandle(register, getHeight);
    const ref = useComposedRefs(forwardedRef, resizeRef);
    return _jsx(Primitive.div, { ...props, ref: ref });
});
ThreadPrimitiveViewportFooter.displayName = "ThreadPrimitive.ViewportFooter";
//# sourceMappingURL=ThreadViewportFooter.js.map