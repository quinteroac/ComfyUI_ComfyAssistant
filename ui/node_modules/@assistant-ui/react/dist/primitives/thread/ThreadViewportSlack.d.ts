import { type FC, type ReactNode } from "react";
export type ThreadViewportSlackProps = {
    /** Threshold at which the user message height clamps to the offset */
    fillClampThreshold?: string;
    /** Offset used when clamping large user messages */
    fillClampOffset?: string;
    children: ReactNode;
};
/**
 * A slot component that provides minimum height to enable scroll anchoring.
 *
 * When using `turnAnchor="top"`, this component ensures there is
 * enough scroll room below the anchor point (last user message) for it to scroll
 * to the top of the viewport. The min-height is applied only to the last
 * assistant message.
 *
 * This component is used internally by MessagePrimitive.Root.
 */
export declare const ThreadPrimitiveViewportSlack: FC<ThreadViewportSlackProps>;
//# sourceMappingURL=ThreadViewportSlack.d.ts.map