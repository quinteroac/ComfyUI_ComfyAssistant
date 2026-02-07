"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { forwardRef } from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { usePopoverScope } from "./scope.js";
export const AssistantModalPrimitiveAnchor = forwardRef(({ __scopeAssistantModal, ...rest }, ref) => {
    const scope = usePopoverScope(__scopeAssistantModal);
    return _jsx(PopoverPrimitive.Anchor, { ...scope, ...rest, ref: ref });
});
AssistantModalPrimitiveAnchor.displayName = "AssistantModalPrimitive.Anchor";
//# sourceMappingURL=AssistantModalAnchor.js.map