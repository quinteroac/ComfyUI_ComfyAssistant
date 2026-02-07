import { type UIMessage } from "ai";
import { type useExternalMessageConverter } from "@assistant-ui/react";
export declare const AISDKMessageConverter: {
    useThreadMessages: ({ messages, isRunning, joinStrategy, metadata, }: {
        messages: UIMessage<unknown, import("ai").UIDataTypes, import("ai").UITools>[];
        isRunning: boolean;
        joinStrategy?: "concat-content" | "none" | undefined;
        metadata?: useExternalMessageConverter.Metadata;
    }) => import("@assistant-ui/react").ThreadMessage[];
    toThreadMessages: (messages: UIMessage<unknown, import("ai").UIDataTypes, import("ai").UITools>[], isRunning?: boolean, metadata?: useExternalMessageConverter.Metadata) => import("@assistant-ui/react").ThreadMessage[];
    toOriginalMessages: (input: import("@assistant-ui/react").ThreadState | import("@assistant-ui/react").ThreadMessage | import("@assistant-ui/react").ThreadMessage["content"][number]) => unknown[];
    toOriginalMessage: (input: import("@assistant-ui/react").ThreadState | import("@assistant-ui/react").ThreadMessage | import("@assistant-ui/react").ThreadMessage["content"][number]) => {};
    useOriginalMessage: () => {};
    useOriginalMessages: () => unknown[];
};
//# sourceMappingURL=convertMessage.d.ts.map