import { Primitive } from "@radix-ui/react-primitive";
import { type ComponentRef, ComponentPropsWithoutRef } from "react";
export declare namespace ThreadPrimitiveViewportFooter {
    type Element = ComponentRef<typeof Primitive.div>;
    type Props = ComponentPropsWithoutRef<typeof Primitive.div>;
}
/**
 * A footer container that measures its height for scroll calculations.
 *
 * This component measures its height and provides it to the viewport context
 * for use in scroll calculations (e.g., ViewportSlack min-height).
 *
 * Multiple ViewportFooter components can be used - their heights are summed.
 *
 * Typically used with `className="sticky bottom-0"` to keep the footer
 * visible at the bottom of the viewport while scrolling.
 *
 * @example
 * ```tsx
 * <ThreadPrimitive.Viewport>
 *   <ThreadPrimitive.Messages components={{ ... }} />
 *   <ThreadPrimitive.ViewportFooter className="sticky bottom-0">
 *     <Composer />
 *   </ThreadPrimitive.ViewportFooter>
 * </ThreadPrimitive.Viewport>
 * ```
 */
export declare const ThreadPrimitiveViewportFooter: import("react").ForwardRefExoticComponent<Omit<import("react").ClassAttributes<HTMLDivElement> & import("react").HTMLAttributes<HTMLDivElement> & {
    asChild?: boolean;
}, "ref"> & import("react").RefAttributes<HTMLDivElement>>;
//# sourceMappingURL=ThreadViewportFooter.d.ts.map