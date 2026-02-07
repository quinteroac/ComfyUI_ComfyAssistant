import { ToolResponse } from "./ToolResponse.js";
import { ToolExecutionStream } from "./ToolExecutionStream.js";
const isStandardSchemaV1 = (schema) => {
    return (typeof schema === "object" &&
        schema !== null &&
        "~standard" in schema &&
        schema["~standard"].version === 1);
};
function getToolResponse(tools, abortSignal, toolCall, human) {
    const tool = tools?.[toolCall.toolName];
    if (!tool || !tool.execute)
        return undefined;
    const getResult = async (toolExecute) => {
        // Check if already aborted before starting
        if (abortSignal.aborted) {
            return new ToolResponse({
                result: "Tool execution was cancelled.",
                isError: true,
            });
        }
        let executeFn = toolExecute;
        if (isStandardSchemaV1(tool.parameters)) {
            let result = tool.parameters["~standard"].validate(toolCall.args);
            if (result instanceof Promise)
                result = await result;
            if (result.issues) {
                executeFn =
                    tool.experimental_onSchemaValidationError ??
                        (() => {
                            throw new Error(`Function parameter validation failed. ${JSON.stringify(result.issues)}`);
                        });
            }
        }
        // Create abort promise that resolves after 2 microtasks
        // This gives tools that handle abort a chance to win the race
        const abortPromise = new Promise((resolve) => {
            const onAbort = () => {
                queueMicrotask(() => {
                    queueMicrotask(() => {
                        resolve(new ToolResponse({
                            result: "Tool execution was cancelled.",
                            isError: true,
                        }));
                    });
                });
            };
            if (abortSignal.aborted) {
                onAbort();
            }
            else {
                abortSignal.addEventListener("abort", onAbort, { once: true });
            }
        });
        const executePromise = (async () => {
            const result = (await executeFn(toolCall.args, {
                toolCallId: toolCall.toolCallId,
                abortSignal,
                human: (payload) => human(toolCall.toolCallId, payload),
            }));
            return ToolResponse.toResponse(result);
        })();
        return Promise.race([executePromise, abortPromise]);
    };
    return getResult(tool.execute);
}
function getToolStreamResponse(tools, abortSignal, reader, context, human) {
    tools?.[context.toolName]?.streamCall?.(reader, {
        toolCallId: context.toolCallId,
        abortSignal,
        human: (payload) => human(context.toolCallId, payload),
    });
}
export async function unstable_runPendingTools(message, tools, abortSignal, human) {
    const toolCallPromises = message.parts
        .filter((part) => part.type === "tool-call")
        .map(async (part) => {
        const promiseOrUndefined = getToolResponse(tools, abortSignal, part, human ??
            (async () => {
                throw new Error("Tool human input is not supported in this context");
            }));
        if (promiseOrUndefined) {
            const result = await promiseOrUndefined;
            return {
                toolCallId: part.toolCallId,
                result,
            };
        }
        return null;
    });
    const toolCallResults = (await Promise.all(toolCallPromises)).filter((result) => result !== null);
    if (toolCallResults.length === 0) {
        return message;
    }
    const toolCallResultsById = toolCallResults.reduce((acc, { toolCallId, result }) => {
        acc[toolCallId] = result;
        return acc;
    }, {});
    const updatedParts = message.parts.map((p) => {
        if (p.type === "tool-call") {
            const toolResponse = toolCallResultsById[p.toolCallId];
            if (toolResponse) {
                return {
                    ...p,
                    state: "result",
                    ...(toolResponse.artifact !== undefined
                        ? { artifact: toolResponse.artifact }
                        : {}),
                    result: toolResponse.result,
                    isError: toolResponse.isError,
                };
            }
        }
        return p;
    });
    return {
        ...message,
        parts: updatedParts,
        content: updatedParts,
    };
}
export function toolResultStream(tools, abortSignal, human, options) {
    const toolsFn = typeof tools === "function" ? tools : () => tools;
    const abortSignalFn = typeof abortSignal === "function" ? abortSignal : () => abortSignal;
    return new ToolExecutionStream({
        execute: (toolCall) => getToolResponse(toolsFn(), abortSignalFn(), toolCall, human),
        streamCall: ({ reader, ...context }) => getToolStreamResponse(toolsFn(), abortSignalFn(), reader, context, human),
        onExecutionStart: options?.onExecutionStart,
        onExecutionEnd: options?.onExecutionEnd,
    });
}
//# sourceMappingURL=toolResultStream.js.map