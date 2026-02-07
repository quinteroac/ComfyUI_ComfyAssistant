"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { Primitive } from "@radix-ui/react-primitive";
import { forwardRef } from "react";
import { useActionBarFloatStatus, HideAndFloatStatus, } from "./useActionBarFloatStatus.js";
/**
 * The root container for action bar components.
 *
 * This component provides intelligent visibility and floating behavior for action bars,
 * automatically hiding and showing based on message state, hover status, and configuration.
 * It supports floating mode for better UX when space is limited.
 *
 * @example
 * ```tsx
 * <ActionBarPrimitive.Root
 *   hideWhenRunning={true}
 *   autohide="not-last"
 *   autohideFloat="single-branch"
 * >
 *   <ActionBarPrimitive.Copy />
 *   <ActionBarPrimitive.Edit />
 *   <ActionBarPrimitive.Reload />
 * </ActionBarPrimitive.Root>
 * ```
 */
export const ActionBarPrimitiveRoot = forwardRef(({ hideWhenRunning, autohide, autohideFloat, ...rest }, ref) => {
    const hideAndfloatStatus = useActionBarFloatStatus({
        hideWhenRunning,
        autohide,
        autohideFloat,
    });
    if (hideAndfloatStatus === HideAndFloatStatus.Hidden)
        return null;
    return (_jsx(Primitive.div, { ...(hideAndfloatStatus === HideAndFloatStatus.Floating
            ? { "data-floating": "true" }
            : null), ...rest, ref: ref }));
});
ActionBarPrimitiveRoot.displayName = "ActionBarPrimitive.Root";
//# sourceMappingURL=ActionBarRoot.js.map