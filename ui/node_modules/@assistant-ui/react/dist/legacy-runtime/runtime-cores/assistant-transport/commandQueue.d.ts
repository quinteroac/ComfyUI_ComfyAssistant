import { AssistantTransportCommand, CommandQueueState, QueuedCommand } from "./types.js";
export declare const createInitialQueueState: () => CommandQueueState;
export declare const useCommandQueue: (opts: {
    onQueue: () => void;
}) => {
    state: CommandQueueState;
    enqueue: (command: AssistantTransportCommand) => void;
    flush: () => QueuedCommand[];
    markDelivered: () => void;
    reset: () => void;
};
//# sourceMappingURL=commandQueue.d.ts.map