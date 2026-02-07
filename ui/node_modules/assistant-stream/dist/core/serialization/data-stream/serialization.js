export class DataStreamChunkEncoder extends TransformStream {
    constructor() {
        super({
            transform: (chunk, controller) => {
                controller.enqueue(`${chunk.type}:${JSON.stringify(chunk.value)}\n`);
            },
        });
    }
}
export class DataStreamChunkDecoder extends TransformStream {
    constructor() {
        super({
            transform: (chunk, controller) => {
                const index = chunk.indexOf(":");
                if (index === -1)
                    throw new Error("Invalid stream part");
                controller.enqueue({
                    type: chunk.slice(0, index),
                    value: JSON.parse(chunk.slice(index + 1)),
                });
            },
        });
    }
}
//# sourceMappingURL=serialization.js.map