import { AssistantTransformStream } from "../utils/stream/AssistantTransformStream.js";
import { PipeableTransformStream } from "../utils/stream/PipeableTransformStream.js";
export class PlainTextEncoder extends PipeableTransformStream {
    headers = new Headers({
        "Content-Type": "text/plain; charset=utf-8",
        "x-vercel-ai-data-stream": "v1",
    });
    constructor() {
        super((readable) => {
            const transform = new TransformStream({
                transform(chunk, controller) {
                    const type = chunk.type;
                    switch (type) {
                        case "text-delta":
                            controller.enqueue(chunk.textDelta);
                            break;
                        case "part-start":
                        case "part-finish":
                        case "step-start":
                        case "step-finish":
                        case "message-finish":
                        case "error":
                            break;
                        default:
                            const unsupportedType = type;
                            throw new Error(`unsupported chunk type: ${unsupportedType}`);
                    }
                },
            });
            return readable
                .pipeThrough(transform)
                .pipeThrough(new TextEncoderStream());
        });
    }
}
export class PlainTextDecoder extends PipeableTransformStream {
    constructor() {
        super((readable) => {
            const transform = new AssistantTransformStream({
                transform(chunk, controller) {
                    controller.appendText(chunk);
                },
            });
            return readable
                .pipeThrough(new TextDecoderStream())
                .pipeThrough(transform);
        });
    }
}
//# sourceMappingURL=PlainText.js.map