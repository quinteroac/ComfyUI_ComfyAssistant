import { AssistantStream } from "../AssistantStream.js";
import { AssistantMessage } from "../utils/types.js";
export declare class AssistantMessageStream {
    readonly readable: ReadableStream<AssistantMessage>;
    constructor(readable: ReadableStream<AssistantMessage>);
    static fromAssistantStream(stream: AssistantStream): AssistantMessageStream;
    unstable_result(): Promise<AssistantMessage>;
    [Symbol.asyncIterator](): {
        next(): Promise<IteratorResult<AssistantMessage, undefined>>;
    };
    tee(): [AssistantMessageStream, AssistantMessageStream];
}
//# sourceMappingURL=AssistantMessageStream.d.ts.map