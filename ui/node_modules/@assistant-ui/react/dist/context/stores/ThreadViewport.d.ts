import type { Unsubscribe } from "../../types/Unsubscribe.js";
export type SizeHandle = {
    /** Update the height */
    setHeight: (height: number) => void;
    /** Unregister this handle */
    unregister: Unsubscribe;
};
export type ThreadViewportState = {
    readonly isAtBottom: boolean;
    readonly scrollToBottom: (config?: {
        behavior?: ScrollBehavior | undefined;
    }) => void;
    readonly onScrollToBottom: (callback: ({ behavior }: {
        behavior: ScrollBehavior;
    }) => void) => Unsubscribe;
    /** Controls scroll anchoring: "top" anchors user messages at top, "bottom" is classic behavior */
    readonly turnAnchor: "top" | "bottom";
    /** Raw height values from registered elements */
    readonly height: {
        /** Total viewport height */
        readonly viewport: number;
        /** Total content inset height (footer, anchor message, etc.) */
        readonly inset: number;
        /** Height of the anchor user message (full height) */
        readonly userMessage: number;
    };
    /** Register a viewport and get a handle to update its height */
    readonly registerViewport: () => SizeHandle;
    /** Register a content inset (footer, anchor message, etc.) and get a handle to update its height */
    readonly registerContentInset: () => SizeHandle;
    /** Register the anchor user message height */
    readonly registerUserMessageHeight: () => SizeHandle;
};
export type ThreadViewportStoreOptions = {
    turnAnchor?: "top" | "bottom" | undefined;
};
export declare const makeThreadViewportStore: (options?: ThreadViewportStoreOptions) => import("zustand").UseBoundStore<import("zustand").StoreApi<ThreadViewportState>>;
//# sourceMappingURL=ThreadViewport.d.ts.map