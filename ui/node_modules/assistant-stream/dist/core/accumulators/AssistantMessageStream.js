import { AssistantMessageAccumulator } from "./assistant-message-accumulator.js";
export class AssistantMessageStream {
    readable;
    constructor(readable) {
        this.readable = readable;
        this.readable = readable;
    }
    static fromAssistantStream(stream) {
        return new AssistantMessageStream(stream.pipeThrough(new AssistantMessageAccumulator()));
    }
    async unstable_result() {
        let last;
        for await (const chunk of this) {
            last = chunk;
        }
        if (!last) {
            return {
                role: "assistant",
                status: { type: "complete", reason: "unknown" },
                parts: [],
                content: [],
                metadata: {
                    unstable_state: null,
                    unstable_data: [],
                    unstable_annotations: [],
                    steps: [],
                    custom: {},
                },
            };
        }
        return last;
    }
    [Symbol.asyncIterator]() {
        const reader = this.readable.getReader();
        return {
            async next() {
                const { done, value } = await reader.read();
                return done ? { done: true, value: undefined } : { done: false, value };
            },
        };
    }
    tee() {
        const [readable1, readable2] = this.readable.tee();
        return [
            new AssistantMessageStream(readable1),
            new AssistantMessageStream(readable2),
        ];
    }
}
//# sourceMappingURL=AssistantMessageStream.js.map