"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef } from "react";
/**
 * The root container for chain of thought components.
 *
 * This component provides a wrapper for chain of thought content,
 * including reasoning and tool-call parts that can be collapsed in an accordion.
 *
 * @example
 * ```tsx
 * <ChainOfThoughtPrimitive.Root>
 *   <ChainOfThoughtPrimitive.AccordionTrigger>
 *     Toggle reasoning
 *   </ChainOfThoughtPrimitive.AccordionTrigger>
 *   <ChainOfThoughtPrimitive.Parts />
 * </ChainOfThoughtPrimitive.Root>
 * ```
 */
export const ChainOfThoughtPrimitiveRoot = forwardRef((props, ref) => {
    return _jsx(Primitive.div, { ...props, ref: ref });
});
ChainOfThoughtPrimitiveRoot.displayName = "ChainOfThoughtPrimitive.Root";
//# sourceMappingURL=ChainOfThoughtRoot.js.map