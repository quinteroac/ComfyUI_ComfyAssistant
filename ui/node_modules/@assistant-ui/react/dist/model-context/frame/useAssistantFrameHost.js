"use client";
import { useEffect } from "react";
import { AssistantFrameHost } from "./AssistantFrameHost.js";
/**
 * React hook that manages the lifecycle of an AssistantFrameHost and its binding to the current AssistantRuntime.
 *
 * Usage example:
 * ```typescript
 * function MyComponent() {
 *   const iframeRef = useRef<HTMLIFrameElement>(null);
 *
 *   useAssistantFrameHost({
 *     iframeRef,
 *     targetOrigin: "https://trusted-domain.com", // optional
 *   });
 *
 *   return <iframe ref={iframeRef} src="..." />;
 * }
 * ```
 */
export const useAssistantFrameHost = ({ iframeRef, targetOrigin = "*", register, }) => {
    useEffect(() => {
        const iframeWindow = iframeRef.current?.contentWindow;
        if (!iframeWindow)
            return;
        const frameHost = new AssistantFrameHost(iframeWindow, targetOrigin);
        const unsubscribe = register(frameHost);
        return () => {
            frameHost.dispose();
            unsubscribe();
        };
    }, [iframeRef, targetOrigin, register]);
};
//# sourceMappingURL=useAssistantFrameHost.js.map