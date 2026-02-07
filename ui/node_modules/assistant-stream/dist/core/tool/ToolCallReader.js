import { promiseWithResolvers } from "../../utils/promiseWithResolvers.js";
import { parsePartialJsonObject, getPartialJsonObjectFieldState, } from "../../utils/json/parse-partial-json-object.js";
import { asAsyncIterableStream, } from "../../utils.js";
// TODO: remove dispose
function getField(obj, fieldPath) {
    let current = obj;
    for (const key of fieldPath) {
        if (current === undefined || current === null) {
            return undefined;
        }
        current = current[key];
    }
    return current;
}
class GetHandle {
    resolve;
    reject;
    disposed = false;
    fieldPath;
    constructor(resolve, reject, fieldPath) {
        this.resolve = resolve;
        this.reject = reject;
        this.fieldPath = fieldPath;
    }
    update(args) {
        if (this.disposed)
            return;
        try {
            // Check if the field is complete
            if (getPartialJsonObjectFieldState(args, this.fieldPath) === "complete") {
                const value = getField(args, this.fieldPath);
                if (value !== undefined) {
                    this.resolve(value);
                    this.dispose();
                }
            }
        }
        catch (e) {
            this.reject(e);
            this.dispose();
        }
    }
    dispose() {
        this.disposed = true;
    }
}
class StreamValuesHandle {
    controller;
    disposed = false;
    fieldPath;
    constructor(controller, fieldPath) {
        this.controller = controller;
        this.fieldPath = fieldPath;
    }
    update(args) {
        if (this.disposed)
            return;
        try {
            const value = getField(args, this.fieldPath);
            if (value !== undefined) {
                this.controller.enqueue(value);
            }
            // Check if the field is complete, if so close the stream
            if (getPartialJsonObjectFieldState(args, this.fieldPath) === "complete") {
                this.controller.close();
                this.dispose();
            }
        }
        catch (e) {
            this.controller.error(e);
            this.dispose();
        }
    }
    dispose() {
        this.disposed = true;
    }
}
class StreamTextHandle {
    controller;
    disposed = false;
    fieldPath;
    lastValue = undefined;
    constructor(controller, fieldPath) {
        this.controller = controller;
        this.fieldPath = fieldPath;
    }
    update(args) {
        if (this.disposed)
            return;
        try {
            const value = getField(args, this.fieldPath);
            if (value !== undefined && typeof value === "string") {
                const delta = value.substring(this.lastValue?.length || 0);
                this.lastValue = value;
                this.controller.enqueue(delta);
            }
            // Check if the field is complete, if so close the stream
            if (getPartialJsonObjectFieldState(args, this.fieldPath) === "complete") {
                this.controller.close();
                this.dispose();
            }
        }
        catch (e) {
            this.controller.error(e);
            this.dispose();
        }
    }
    dispose() {
        this.disposed = true;
    }
}
class ForEachHandle {
    controller;
    disposed = false;
    fieldPath;
    processedIndexes = new Set();
    constructor(controller, fieldPath) {
        this.controller = controller;
        this.fieldPath = fieldPath;
    }
    update(args) {
        if (this.disposed)
            return;
        try {
            const array = getField(args, this.fieldPath);
            if (!Array.isArray(array)) {
                return;
            }
            // Check each array element and emit completed ones that haven't been processed
            for (let i = 0; i < array.length; i++) {
                if (!this.processedIndexes.has(i)) {
                    const elementPath = [...this.fieldPath, i];
                    if (getPartialJsonObjectFieldState(args, elementPath) === "complete") {
                        this.controller.enqueue(array[i]);
                        this.processedIndexes.add(i);
                    }
                }
            }
            // Check if the entire array is complete
            if (getPartialJsonObjectFieldState(args, this.fieldPath) === "complete") {
                this.controller.close();
                this.dispose();
            }
        }
        catch (e) {
            this.controller.error(e);
            this.dispose();
        }
    }
    dispose() {
        this.disposed = true;
    }
}
// Implementation of ToolCallReader that uses stream of partial JSON
export class ToolCallArgsReaderImpl {
    argTextDeltas;
    handles = new Set();
    args = parsePartialJsonObject("");
    constructor(argTextDeltas) {
        this.argTextDeltas = argTextDeltas;
        this.processStream();
    }
    async processStream() {
        try {
            let accumulatedText = "";
            const reader = this.argTextDeltas.getReader();
            while (true) {
                const { value, done } = await reader.read();
                if (done)
                    break;
                accumulatedText += value;
                const parsedArgs = parsePartialJsonObject(accumulatedText);
                if (parsedArgs !== undefined) {
                    this.args = parsedArgs;
                    // Notify all handles of the updated args
                    for (const handle of this.handles) {
                        handle.update(parsedArgs);
                    }
                }
            }
        }
        catch (error) {
            console.error("Error processing argument stream:", error);
            // Notify handles of the error
            for (const handle of this.handles) {
                handle.dispose();
            }
        }
    }
    get(...fieldPath) {
        return new Promise((resolve, reject) => {
            const handle = new GetHandle(resolve, reject, fieldPath);
            // Check if the field is already complete in current args
            if (this.args &&
                getPartialJsonObjectFieldState(this.args, fieldPath) === "complete") {
                const value = getField(this.args, fieldPath);
                if (value !== undefined) {
                    resolve(value);
                    return;
                }
            }
            this.handles.add(handle);
            handle.update(this.args);
        });
    }
    streamValues(...fieldPath) {
        // Use a type assertion to convert the complex TypePath to a simple array
        const simplePath = fieldPath;
        const stream = new ReadableStream({
            start: (controller) => {
                const handle = new StreamValuesHandle(controller, simplePath);
                this.handles.add(handle);
                // Check current args immediately
                handle.update(this.args);
            },
            cancel: () => {
                // Find and dispose the corresponding handle
                for (const handle of this.handles) {
                    if (handle instanceof StreamValuesHandle) {
                        handle.dispose();
                        this.handles.delete(handle);
                        break;
                    }
                }
            },
        });
        return asAsyncIterableStream(stream);
    }
    streamText(...fieldPath) {
        // Use a type assertion to convert the complex TypePath to a simple array
        const simplePath = fieldPath;
        const stream = new ReadableStream({
            start: (controller) => {
                const handle = new StreamTextHandle(controller, simplePath);
                this.handles.add(handle);
                // Check current args immediately
                handle.update(this.args);
            },
            cancel: () => {
                // Find and dispose the corresponding handle
                for (const handle of this.handles) {
                    if (handle instanceof StreamTextHandle) {
                        handle.dispose();
                        this.handles.delete(handle);
                        break;
                    }
                }
            },
        });
        return asAsyncIterableStream(stream);
    }
    forEach(...fieldPath) {
        // Use a type assertion to convert the complex TypePath to a simple array
        const simplePath = fieldPath;
        const stream = new ReadableStream({
            start: (controller) => {
                const handle = new ForEachHandle(controller, simplePath);
                this.handles.add(handle);
                // Check current args immediately
                handle.update(this.args);
            },
            cancel: () => {
                // Find and dispose the corresponding handle
                for (const handle of this.handles) {
                    if (handle instanceof ForEachHandle) {
                        handle.dispose();
                        this.handles.delete(handle);
                        break;
                    }
                }
            },
        });
        return asAsyncIterableStream(stream);
    }
}
export class ToolCallResponseReaderImpl {
    promise;
    constructor(promise) {
        this.promise = promise;
    }
    get() {
        return this.promise;
    }
}
export class ToolCallReaderImpl {
    args;
    response;
    writable;
    resolve;
    argsText = "";
    constructor() {
        const stream = new TransformStream();
        this.writable = stream.writable;
        this.args = new ToolCallArgsReaderImpl(stream.readable);
        const { promise, resolve } = promiseWithResolvers();
        this.resolve = resolve;
        this.response = new ToolCallResponseReaderImpl(promise);
    }
    async appendArgsTextDelta(text) {
        const writer = this.writable.getWriter();
        try {
            await writer.write(text);
        }
        catch (err) {
            console.warn(err);
        }
        finally {
            writer.releaseLock();
        }
        this.argsText += text;
    }
    setResponse(value) {
        this.resolve(value);
    }
    result = {
        get: async () => {
            const response = await this.response.get();
            return response.result;
        },
    };
}
//# sourceMappingURL=ToolCallReader.js.map