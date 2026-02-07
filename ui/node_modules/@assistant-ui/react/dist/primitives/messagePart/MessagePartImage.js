"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef } from "react";
import { useMessagePartImage } from "./useMessagePartImage.js";
/**
 * Renders an image from the current message part context.
 *
 * This component displays image content from the current message part,
 * automatically setting the src attribute from the message part's image data.
 *
 * @example
 * ```tsx
 * <MessagePartPrimitive.Image
 *   alt="Generated image"
 *   className="message-image"
 *   style={{ maxWidth: '100%' }}
 * />
 * ```
 */
export const MessagePartPrimitiveImage = forwardRef((props, forwardedRef) => {
    const { image } = useMessagePartImage();
    return _jsx(Primitive.img, { src: image, ...props, ref: forwardedRef });
});
MessagePartPrimitiveImage.displayName = "MessagePartPrimitive.Image";
//# sourceMappingURL=MessagePartImage.js.map