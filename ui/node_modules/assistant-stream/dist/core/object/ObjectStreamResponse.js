import { PipeableTransformStream } from "../utils/stream/PipeableTransformStream.js";
import { ObjectStreamAccumulator } from "./ObjectStreamAccumulator.js";
import { SSEDecoder, SSEEncoder } from "../utils/stream/SSE.js";
export class ObjectStreamEncoder extends PipeableTransformStream {
    constructor() {
        super((readable) => readable
            .pipeThrough((() => {
            class ObjectStreamTransformer {
                #isFirstChunk = true;
                start() {
                    // Nothing needed here since we initialize in the field declaration
                }
                transform(chunk, controller) {
                    if (this.#isFirstChunk &&
                        chunk.snapshot &&
                        Object.keys(chunk.snapshot).length > 0) {
                        // For the first chunk, if there's an initial state that's not empty,
                        // prepend a set operation for the initial state
                        controller.enqueue([
                            { type: "set", path: [], value: chunk.snapshot },
                            ...chunk.operations,
                        ]);
                    }
                    else {
                        controller.enqueue(chunk.operations);
                    }
                    this.#isFirstChunk = false;
                }
            }
            return new TransformStream(new ObjectStreamTransformer());
        })())
            .pipeThrough(new SSEEncoder()));
    }
}
export class ObjectStreamDecoder extends PipeableTransformStream {
    constructor() {
        const accumulator = new ObjectStreamAccumulator();
        super((readable) => readable
            .pipeThrough(new SSEDecoder())
            .pipeThrough(new TransformStream({
            transform(operations, controller) {
                accumulator.append(operations);
                controller.enqueue({
                    snapshot: accumulator.state,
                    operations,
                });
            },
        })));
    }
}
export class ObjectStreamResponse extends Response {
    constructor(body) {
        super(body.pipeThrough(new ObjectStreamEncoder()), {
            headers: new Headers({
                "Content-Type": "text/event-stream",
                "Cache-Control": "no-cache",
                Connection: "keep-alive",
                "Assistant-Stream-Format": "object-stream/v0",
            }),
        });
    }
}
export const fromObjectStreamResponse = (response) => {
    if (!response.ok)
        throw new Error(`Response failed, status ${response.status}`);
    if (!response.body)
        throw new Error("Response body is null");
    if (response.headers.get("Content-Type") !== "text/event-stream") {
        throw new Error("Response is not an event stream");
    }
    if (response.headers.get("Assistant-Stream-Format") !== "object-stream/v0") {
        throw new Error("Unsupported Assistant-Stream-Format header");
    }
    return response.body.pipeThrough(new ObjectStreamDecoder());
};
//# sourceMappingURL=ObjectStreamResponse.js.map