"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { forwardRef } from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { useDropdownMenuScope } from "./scope.js";
export const ThreadListItemMorePrimitiveTrigger = forwardRef(({ __scopeThreadListItemMore, ...rest }, ref) => {
    const scope = useDropdownMenuScope(__scopeThreadListItemMore);
    return _jsx(DropdownMenuPrimitive.Trigger, { ...scope, ...rest, ref: ref });
});
ThreadListItemMorePrimitiveTrigger.displayName =
    "ThreadListItemMorePrimitive.Trigger";
//# sourceMappingURL=ThreadListItemMoreTrigger.js.map