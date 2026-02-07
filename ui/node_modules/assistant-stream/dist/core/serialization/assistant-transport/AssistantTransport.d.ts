import { AssistantStreamChunk } from "../../AssistantStreamChunk.js";
import { PipeableTransformStream } from "../../utils/stream/PipeableTransformStream.js";
import { AssistantStreamEncoder } from "../../AssistantStream.js";
/**
 * AssistantTransportEncoder encodes AssistantStreamChunks into SSE format
 * and emits [DONE] when the stream completes.
 */
export declare class AssistantTransportEncoder extends PipeableTransformStream<AssistantStreamChunk, Uint8Array<ArrayBuffer>> implements AssistantStreamEncoder {
    headers: Headers;
    constructor();
}
/**
 * AssistantTransportDecoder decodes SSE format into AssistantStreamChunks.
 * It stops decoding when it encounters [DONE].
 */
export declare class AssistantTransportDecoder extends PipeableTransformStream<Uint8Array<ArrayBuffer>, AssistantStreamChunk> {
    constructor();
}
//# sourceMappingURL=AssistantTransport.d.ts.map