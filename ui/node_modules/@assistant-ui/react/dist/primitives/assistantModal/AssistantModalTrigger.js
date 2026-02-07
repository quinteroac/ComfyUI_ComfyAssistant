import { jsx as _jsx } from "react/jsx-runtime";
import { forwardRef } from "react";
import * as PopoverPrimitive from "@radix-ui/react-popover";
import { usePopoverScope } from "./scope.js";
export const AssistantModalPrimitiveTrigger = forwardRef(({ __scopeAssistantModal, ...rest }, ref) => {
    const scope = usePopoverScope(__scopeAssistantModal);
    return _jsx(PopoverPrimitive.Trigger, { ...scope, ...rest, ref: ref });
});
AssistantModalPrimitiveTrigger.displayName = "AssistantModalPrimitive.Trigger";
//# sourceMappingURL=AssistantModalTrigger.js.map