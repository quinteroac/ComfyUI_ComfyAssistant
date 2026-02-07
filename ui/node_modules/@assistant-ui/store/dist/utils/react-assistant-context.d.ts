import React from "react";
import type { AssistantClient } from "../types/client.js";
/** Default context value - throws "wrap in AuiProvider" error */
export declare const DefaultAssistantClient: AssistantClient;
/** Root prototype for created clients - throws "scope not defined" error */
export declare const createRootAssistantClient: () => AssistantClient;
export declare const useAssistantContextValue: () => AssistantClient;
/**
 * Provider component for AssistantClient
 *
 * @example
 * ```typescript
 * <AuiProvider value={aui}>
 *   <YourApp />
 * </AuiProvider>
 * ```
 */
export declare const AuiProvider: ({ value, children, }: {
    value: AssistantClient;
    children: React.ReactNode;
}) => React.ReactElement;
//# sourceMappingURL=react-assistant-context.d.ts.map