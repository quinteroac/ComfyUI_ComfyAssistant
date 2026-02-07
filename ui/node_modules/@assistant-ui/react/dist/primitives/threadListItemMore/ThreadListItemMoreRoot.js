"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
import { useDropdownMenuScope } from "./scope.js";
export const ThreadListItemMorePrimitiveRoot = ({ __scopeThreadListItemMore, ...rest }) => {
    const scope = useDropdownMenuScope(__scopeThreadListItemMore);
    return _jsx(DropdownMenuPrimitive.Root, { ...scope, ...rest });
};
ThreadListItemMorePrimitiveRoot.displayName =
    "ThreadListItemMorePrimitive.Root";
//# sourceMappingURL=ThreadListItemMoreRoot.js.map