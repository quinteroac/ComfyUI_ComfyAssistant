import { jsx as _jsx } from "react/jsx-runtime";
import { forwardRef, } from "react";
import { Primitive } from "@radix-ui/react-primitive";
import { composeEventHandlers } from "@radix-ui/primitive";
export const createActionButton = (displayName, useActionButton, forwardProps = []) => {
    const ActionButton = forwardRef((props, forwardedRef) => {
        const forwardedProps = {};
        const primitiveProps = {};
        Object.keys(props).forEach((key) => {
            if (forwardProps.includes(key)) {
                forwardedProps[key] = props[key];
            }
            else {
                primitiveProps[key] = props[key];
            }
        });
        const callback = useActionButton(forwardedProps) ?? undefined;
        return (_jsx(Primitive.button, { type: "button", ...primitiveProps, ref: forwardedRef, disabled: primitiveProps.disabled || !callback, onClick: composeEventHandlers(primitiveProps.onClick, callback) }));
    });
    ActionButton.displayName = displayName;
    return ActionButton;
};
//# sourceMappingURL=createActionButton.js.map