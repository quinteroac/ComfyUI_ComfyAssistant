"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef } from "react";
export const ErrorPrimitiveRoot = forwardRef((props, forwardRef) => {
    return _jsx(Primitive.div, { role: "alert", ...props, ref: forwardRef });
});
ErrorPrimitiveRoot.displayName = "ErrorPrimitive.Root";
//# sourceMappingURL=ErrorRoot.js.map