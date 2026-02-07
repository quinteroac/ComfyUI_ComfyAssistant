import { useCallbackRef } from "@radix-ui/react-use-callback-ref";
import { useCallback } from "react";
import { useManagedRef } from "./useManagedRef.js";
export const useOnResizeContent = (callback) => {
    const callbackRef = useCallbackRef(callback);
    const refCallback = useCallback((el) => {
        const resizeObserver = new ResizeObserver(() => {
            callbackRef();
        });
        const mutationObserver = new MutationObserver((mutations) => {
            // Filter out style-only attribute mutations to prevent feedback loops
            // with components like ThreadViewportSlack that write styles in response
            // to viewport changes
            const hasRelevantMutation = mutations.some((m) => m.type !== "attributes" || m.attributeName !== "style");
            if (hasRelevantMutation) {
                callbackRef();
            }
        });
        resizeObserver.observe(el);
        mutationObserver.observe(el, {
            childList: true,
            subtree: true,
            attributes: true,
            characterData: true,
        });
        return () => {
            resizeObserver.disconnect();
            mutationObserver.disconnect();
        };
    }, [callbackRef]);
    return useManagedRef(refCallback);
};
//# sourceMappingURL=useOnResizeContent.js.map