"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { forwardRef } from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { useDropdownMenuScope } from "./scope.js";
export const ThreadListItemMorePrimitiveSeparator = forwardRef(({ __scopeThreadListItemMore, ...rest }, ref) => {
    const scope = useDropdownMenuScope(__scopeThreadListItemMore);
    return _jsx(DropdownMenuPrimitive.Separator, { ...scope, ...rest, ref: ref });
});
ThreadListItemMorePrimitiveSeparator.displayName =
    "ThreadListItemMorePrimitive.Separator";
//# sourceMappingURL=ThreadListItemMoreSeparator.js.map