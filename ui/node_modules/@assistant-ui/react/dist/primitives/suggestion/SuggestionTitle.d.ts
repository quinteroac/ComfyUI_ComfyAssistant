import { Primitive } from "@radix-ui/react-primitive";
import { type ElementRef, ComponentPropsWithoutRef } from "react";
export declare namespace SuggestionPrimitiveTitle {
    type Element = ElementRef<typeof Primitive.span>;
    type Props = ComponentPropsWithoutRef<typeof Primitive.span>;
}
/**
 * Renders the title of the suggestion.
 *
 * @example
 * ```tsx
 * <SuggestionPrimitive.Title />
 * ```
 */
export declare const SuggestionPrimitiveTitle: import("react").ForwardRefExoticComponent<Omit<import("react").ClassAttributes<HTMLSpanElement> & import("react").HTMLAttributes<HTMLSpanElement> & {
    asChild?: boolean;
}, "ref"> & import("react").RefAttributes<HTMLSpanElement>>;
//# sourceMappingURL=SuggestionTitle.d.ts.map