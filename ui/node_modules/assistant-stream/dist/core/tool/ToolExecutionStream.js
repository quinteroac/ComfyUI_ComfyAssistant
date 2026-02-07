import sjson from "secure-json-parse";
import { AssistantMetaTransformStream, } from "../utils/stream/AssistantMetaTransformStream.js";
import { PipeableTransformStream } from "../utils/stream/PipeableTransformStream.js";
import { ToolResponse } from "./ToolResponse.js";
import { withPromiseOrValue } from "../utils/withPromiseOrValue.js";
import { ToolCallReaderImpl } from "./ToolCallReader.js";
export class ToolExecutionStream extends PipeableTransformStream {
    constructor(options) {
        const toolCallPromises = new Map();
        const toolCallControllers = new Map();
        super((readable) => {
            const transform = new TransformStream({
                transform(chunk, controller) {
                    // forward everything
                    if (chunk.type !== "part-finish" || chunk.meta.type !== "tool-call") {
                        controller.enqueue(chunk);
                    }
                    const type = chunk.type;
                    switch (type) {
                        case "part-start":
                            if (chunk.part.type === "tool-call") {
                                const reader = new ToolCallReaderImpl();
                                toolCallControllers.set(chunk.part.toolCallId, reader);
                                options.streamCall({
                                    reader,
                                    toolCallId: chunk.part.toolCallId,
                                    toolName: chunk.part.toolName,
                                });
                            }
                            break;
                        case "text-delta": {
                            if (chunk.meta.type === "tool-call") {
                                const toolCallId = chunk.meta.toolCallId;
                                const controller = toolCallControllers.get(toolCallId);
                                if (!controller)
                                    throw new Error("No controller found for tool call");
                                controller.appendArgsTextDelta(chunk.textDelta);
                            }
                            break;
                        }
                        case "result": {
                            if (chunk.meta.type !== "tool-call")
                                break;
                            const { toolCallId } = chunk.meta;
                            const controller = toolCallControllers.get(toolCallId);
                            if (!controller)
                                throw new Error("No controller found for tool call");
                            controller.setResponse(new ToolResponse({
                                result: chunk.result,
                                artifact: chunk.artifact,
                                isError: chunk.isError,
                            }));
                            break;
                        }
                        case "tool-call-args-text-finish": {
                            if (chunk.meta.type !== "tool-call")
                                break;
                            const { toolCallId, toolName } = chunk.meta;
                            const streamController = toolCallControllers.get(toolCallId);
                            if (!streamController)
                                throw new Error("No controller found for tool call");
                            let isExecuting = false;
                            const promise = withPromiseOrValue(() => {
                                let args;
                                try {
                                    args = sjson.parse(streamController.argsText);
                                }
                                catch (e) {
                                    throw new Error(`Function parameter parsing failed. ${JSON.stringify(e.message)}`);
                                }
                                const executeResult = options.execute({
                                    toolCallId,
                                    toolName,
                                    args,
                                });
                                // Only mark as executing if the tool has frontend execution
                                if (executeResult !== undefined) {
                                    isExecuting = true;
                                    options.onExecutionStart?.(toolCallId, toolName);
                                }
                                return executeResult;
                            }, (c) => {
                                if (isExecuting) {
                                    options.onExecutionEnd?.(toolCallId, toolName);
                                }
                                if (c === undefined)
                                    return;
                                // TODO how to handle new ToolResult({ result: undefined })?
                                const result = new ToolResponse({
                                    artifact: c.artifact,
                                    result: c.result,
                                    isError: c.isError,
                                });
                                streamController.setResponse(result);
                                controller.enqueue({
                                    type: "result",
                                    path: chunk.path,
                                    ...result,
                                });
                            }, (e) => {
                                if (isExecuting) {
                                    options.onExecutionEnd?.(toolCallId, toolName);
                                }
                                const result = new ToolResponse({
                                    result: String(e),
                                    isError: true,
                                });
                                streamController.setResponse(result);
                                controller.enqueue({
                                    type: "result",
                                    path: chunk.path,
                                    ...result,
                                });
                            });
                            if (promise) {
                                toolCallPromises.set(toolCallId, promise);
                            }
                            break;
                        }
                        case "part-finish": {
                            if (chunk.meta.type !== "tool-call")
                                break;
                            const { toolCallId } = chunk.meta;
                            const toolCallPromise = toolCallPromises.get(toolCallId);
                            if (toolCallPromise) {
                                toolCallPromise.then(() => {
                                    toolCallPromises.delete(toolCallId);
                                    toolCallControllers.delete(toolCallId);
                                    controller.enqueue(chunk);
                                });
                            }
                            else {
                                controller.enqueue(chunk);
                            }
                        }
                    }
                },
                async flush() {
                    await Promise.all(toolCallPromises.values());
                },
            });
            return readable
                .pipeThrough(new AssistantMetaTransformStream())
                .pipeThrough(transform);
        });
    }
}
//# sourceMappingURL=ToolExecutionStream.js.map