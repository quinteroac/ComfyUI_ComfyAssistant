import { ThreadState } from "../../runtime/index.js";
import { ThreadMessage } from "../../../types/index.js";
import { useExternalMessageConverter } from "./external-message-converter.js";
export declare const createMessageConverter: <T extends object>(callback: useExternalMessageConverter.Callback<T>) => {
    useThreadMessages: ({ messages, isRunning, joinStrategy, metadata, }: {
        messages: T[];
        isRunning: boolean;
        joinStrategy?: "concat-content" | "none" | undefined;
        metadata?: useExternalMessageConverter.Metadata;
    }) => ThreadMessage[];
    toThreadMessages: (messages: T[], isRunning?: boolean, metadata?: useExternalMessageConverter.Metadata) => ThreadMessage[];
    toOriginalMessages: (input: ThreadState | ThreadMessage | ThreadMessage["content"][number]) => unknown[];
    toOriginalMessage: (input: ThreadState | ThreadMessage | ThreadMessage["content"][number]) => {};
    useOriginalMessage: () => {};
    useOriginalMessages: () => unknown[];
};
//# sourceMappingURL=createMessageConverter.d.ts.map