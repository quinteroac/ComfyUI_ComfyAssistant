export class PipeableTransformStream extends TransformStream {
    constructor(transform) {
        super();
        const readable = transform(super.readable);
        Object.defineProperty(this, "readable", {
            value: readable,
            writable: false,
        });
    }
}
//# sourceMappingURL=PipeableTransformStream.js.map