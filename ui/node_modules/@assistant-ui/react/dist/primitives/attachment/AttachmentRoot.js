"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef } from "react";
/**
 * The root container component for an attachment.
 *
 * This component provides the foundational wrapper for attachment-related components
 * and content. It serves as the context provider for attachment state and actions.
 *
 * @example
 * ```tsx
 * <AttachmentPrimitive.Root>
 *   <AttachmentPrimitive.Name />
 *   <AttachmentPrimitive.Remove />
 * </AttachmentPrimitive.Root>
 * ```
 */
export const AttachmentPrimitiveRoot = forwardRef((props, ref) => {
    return _jsx(Primitive.div, { ...props, ref: ref });
});
AttachmentPrimitiveRoot.displayName = "AttachmentPrimitive.Root";
//# sourceMappingURL=AttachmentRoot.js.map