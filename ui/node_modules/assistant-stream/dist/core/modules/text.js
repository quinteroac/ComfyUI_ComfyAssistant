class TextStreamControllerImpl {
    _controller;
    _isClosed = false;
    constructor(controller) {
        this._controller = controller;
    }
    append(textDelta) {
        this._controller.enqueue({
            type: "text-delta",
            path: [],
            textDelta,
        });
        return this;
    }
    close() {
        if (this._isClosed)
            return;
        this._isClosed = true;
        this._controller.enqueue({
            type: "part-finish",
            path: [],
        });
        this._controller.close();
    }
}
export const createTextStream = (readable) => {
    return new ReadableStream({
        start(c) {
            return readable.start?.(new TextStreamControllerImpl(c));
        },
        pull(c) {
            return readable.pull?.(new TextStreamControllerImpl(c));
        },
        cancel(c) {
            return readable.cancel?.(c);
        },
    });
};
export const createTextStreamController = () => {
    let controller;
    const stream = createTextStream({
        start(c) {
            controller = c;
        },
    });
    return [stream, controller];
};
//# sourceMappingURL=text.js.map