import { Primitive } from "@radix-ui/react-primitive";
import { type ElementRef, ComponentPropsWithoutRef } from "react";
export declare namespace SuggestionPrimitiveDescription {
    type Element = ElementRef<typeof Primitive.span>;
    type Props = ComponentPropsWithoutRef<typeof Primitive.span>;
}
/**
 * Renders the description/label of the suggestion.
 *
 * @example
 * ```tsx
 * <SuggestionPrimitive.Description />
 * ```
 */
export declare const SuggestionPrimitiveDescription: import("react").ForwardRefExoticComponent<Omit<import("react").ClassAttributes<HTMLSpanElement> & import("react").HTMLAttributes<HTMLSpanElement> & {
    asChild?: boolean;
}, "ref"> & import("react").RefAttributes<HTMLSpanElement>>;
//# sourceMappingURL=SuggestionDescription.d.ts.map