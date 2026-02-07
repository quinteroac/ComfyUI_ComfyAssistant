"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef } from "react";
/**
 * The root container component for a thread.
 *
 * This component serves as the foundational wrapper for all thread-related components.
 * It provides the basic structure and context needed for thread functionality.
 *
 * @example
 * ```tsx
 * <ThreadPrimitive.Root>
 *   <ThreadPrimitive.Viewport>
 *     <ThreadPrimitive.Messages components={{ Message: MyMessage }} />
 *   </ThreadPrimitive.Viewport>
 * </ThreadPrimitive.Root>
 * ```
 */
export const ThreadPrimitiveRoot = forwardRef((props, ref) => {
    return _jsx(Primitive.div, { ...props, ref: ref });
});
ThreadPrimitiveRoot.displayName = "ThreadPrimitive.Root";
//# sourceMappingURL=ThreadRoot.js.map