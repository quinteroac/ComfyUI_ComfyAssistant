import { AssistantStreamChunk } from "../../AssistantStreamChunk.js";
import { PipeableTransformStream } from "../../utils/stream/PipeableTransformStream.js";
import { AssistantStreamEncoder } from "../../AssistantStream.js";
export declare class DataStreamEncoder extends PipeableTransformStream<AssistantStreamChunk, Uint8Array<ArrayBuffer>> implements AssistantStreamEncoder {
    headers: Headers;
    constructor();
}
export declare class DataStreamDecoder extends PipeableTransformStream<Uint8Array<ArrayBuffer>, AssistantStreamChunk> {
    constructor();
}
//# sourceMappingURL=DataStream.d.ts.map