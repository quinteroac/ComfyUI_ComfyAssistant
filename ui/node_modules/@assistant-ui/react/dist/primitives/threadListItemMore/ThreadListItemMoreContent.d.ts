import { ComponentPropsWithoutRef, ComponentRef } from "react";
import * as DropdownMenuPrimitive from "@radix-ui/react-dropdown-menu";
export declare namespace ThreadListItemMorePrimitiveContent {
    type Element = ComponentRef<typeof DropdownMenuPrimitive.Content>;
    type Props = ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Content> & {
        portalProps?: ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Portal> | undefined;
    };
}
export declare const ThreadListItemMorePrimitiveContent: import("react").ForwardRefExoticComponent<Omit<DropdownMenuPrimitive.DropdownMenuContentProps & import("react").RefAttributes<HTMLDivElement>, "ref"> & {
    portalProps?: ComponentPropsWithoutRef<typeof DropdownMenuPrimitive.Portal> | undefined;
} & import("react").RefAttributes<HTMLDivElement>>;
//# sourceMappingURL=ThreadListItemMoreContent.d.ts.map