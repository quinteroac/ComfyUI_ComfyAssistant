"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef } from "react";
import { If } from "../message/index.js";
/**
 * The root container for branch picker components.
 *
 * This component provides a container for branch navigation controls,
 * with optional conditional rendering based on the number of available branches.
 * It integrates with the message branching system to allow users to navigate
 * between different response variations.
 *
 * @example
 * ```tsx
 * <BranchPickerPrimitive.Root hideWhenSingleBranch={true}>
 *   <BranchPickerPrimitive.Previous />
 *   <BranchPickerPrimitive.Count />
 *   <BranchPickerPrimitive.Next />
 * </BranchPickerPrimitive.Root>
 * ```
 */
export const BranchPickerPrimitiveRoot = forwardRef(({ hideWhenSingleBranch, ...rest }, ref) => {
    return (_jsx(If, { hasBranches: hideWhenSingleBranch ? true : undefined, children: _jsx(Primitive.div, { ...rest, ref: ref }) }));
});
BranchPickerPrimitiveRoot.displayName = "BranchPickerPrimitive.Root";
//# sourceMappingURL=BranchPickerRoot.js.map