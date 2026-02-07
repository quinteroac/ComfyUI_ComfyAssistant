import { AssistantStreamChunk } from "../AssistantStreamChunk.js";
import { AssistantMessage } from "../utils/types.js";
import { ReadonlyJSONValue } from "../../utils.js";
export declare const createInitialMessage: ({ unstable_state, }?: {
    unstable_state?: ReadonlyJSONValue;
}) => AssistantMessage;
export declare class AssistantMessageAccumulator extends TransformStream<AssistantStreamChunk, AssistantMessage> {
    constructor({ initialMessage, throttle, onError, }?: {
        initialMessage?: AssistantMessage;
        throttle?: boolean;
        onError?: (error: string) => void;
    });
}
//# sourceMappingURL=assistant-message-accumulator.d.ts.map