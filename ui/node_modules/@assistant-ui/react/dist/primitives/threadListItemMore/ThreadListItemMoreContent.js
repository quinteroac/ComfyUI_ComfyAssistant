"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { forwardRef } from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { useDropdownMenuScope } from "./scope.js";
export const ThreadListItemMorePrimitiveContent = forwardRef(({ __scopeThreadListItemMore, portalProps, sideOffset = 4, ...props }, forwardedRef) => {
    const scope = useDropdownMenuScope(__scopeThreadListItemMore);
    return (_jsx(DropdownMenuPrimitive.Portal, { ...scope, ...portalProps, children: _jsx(DropdownMenuPrimitive.Content, { ...scope, ...props, ref: forwardedRef, sideOffset: sideOffset }) }));
});
ThreadListItemMorePrimitiveContent.displayName =
    "ThreadListItemMorePrimitive.Content";
//# sourceMappingURL=ThreadListItemMoreContent.js.map