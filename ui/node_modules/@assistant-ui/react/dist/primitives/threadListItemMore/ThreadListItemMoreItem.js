"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { forwardRef } from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { useDropdownMenuScope } from "./scope.js";
export const ThreadListItemMorePrimitiveItem = forwardRef(({ __scopeThreadListItemMore, ...rest }, ref) => {
    const scope = useDropdownMenuScope(__scopeThreadListItemMore);
    return _jsx(DropdownMenuPrimitive.Item, { ...scope, ...rest, ref: ref });
});
ThreadListItemMorePrimitiveItem.displayName =
    "ThreadListItemMorePrimitive.Item";
//# sourceMappingURL=ThreadListItemMoreItem.js.map