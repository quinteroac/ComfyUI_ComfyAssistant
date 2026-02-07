/**
 * Generic message types for framework-agnostic LLM message interchange.
 * These types represent a common format that can be converted to/from
 * various LLM provider formats (AI SDK, LangChain, etc.).
 */
const IMAGE_MEDIA_TYPES = {
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    png: "image/png",
    gif: "image/gif",
    webp: "image/webp",
    svg: "image/svg+xml",
    avif: "image/avif",
    bmp: "image/bmp",
    ico: "image/x-icon",
    tiff: "image/tiff",
    tif: "image/tiff",
    heic: "image/heic",
    heif: "image/heif",
};
function inferImageMediaType(url) {
    // Handle data URLs: data:[<mediatype>][;base64],<data>
    if (url.startsWith("data:")) {
        const match = url.match(/^data:([^;,]+)/);
        if (match?.[1])
            return match[1];
    }
    // Extract extension from URL path, ignoring query string and hash
    const [pathWithoutParams = ""] = url.split(/[?#]/);
    const ext = pathWithoutParams.split(".").pop()?.toLowerCase() ?? "";
    return IMAGE_MEDIA_TYPES[ext] ?? "image/png";
}
function toUrlOrString(value) {
    try {
        return new URL(value);
    }
    catch {
        return value;
    }
}
function processToolCall(part, accumulator) {
    if (!part.toolCallId || !part.toolName)
        return false;
    accumulator.textParts.push({
        type: "tool-call",
        toolCallId: part.toolCallId,
        toolName: part.toolName,
        args: part.args ?? {},
    });
    if (part.result !== undefined) {
        const toolResult = {
            type: "tool-result",
            toolCallId: part.toolCallId,
            toolName: part.toolName,
            result: part.result,
        };
        if (part.isError) {
            toolResult.isError = true;
        }
        accumulator.toolResults.push(toolResult);
        return true;
    }
    return false;
}
function flushAccumulator(accumulator, result) {
    if (accumulator.textParts.length > 0) {
        result.push({ role: "assistant", content: accumulator.textParts });
        accumulator.textParts = [];
    }
    if (accumulator.toolResults.length > 0) {
        result.push({ role: "tool", content: accumulator.toolResults });
        accumulator.toolResults = [];
    }
}
function convertSystemMessage(message, result) {
    const textPart = message.content.find((p) => p.type === "text");
    if (textPart?.text) {
        result.push({ role: "system", content: textPart.text });
    }
}
function convertUserMessage(message, result) {
    const attachments = message.attachments ?? [];
    const allContent = [
        ...message.content,
        ...attachments.flatMap((a) => a.content),
    ];
    const content = [];
    for (const part of allContent) {
        if (part.type === "text" && part.text) {
            content.push({ type: "text", text: part.text });
        }
        else if (part.type === "image" && part.image) {
            content.push({
                type: "file",
                data: toUrlOrString(part.image),
                mediaType: inferImageMediaType(part.image),
            });
        }
        else if (part.type === "file" && part.data && part.mimeType) {
            content.push({
                type: "file",
                data: toUrlOrString(part.data),
                mediaType: part.mimeType,
            });
        }
    }
    if (content.length > 0) {
        result.push({ role: "user", content });
    }
}
function convertAssistantMessage(message, result) {
    const accumulator = {
        textParts: [],
        toolResults: [],
    };
    let hasPendingToolResults = false;
    for (const part of message.content) {
        if (part.type === "text" && part.text) {
            // Flush pending tool results before adding more text
            if (hasPendingToolResults) {
                flushAccumulator(accumulator, result);
                hasPendingToolResults = false;
            }
            accumulator.textParts.push({ type: "text", text: part.text });
        }
        else if (part.type === "tool-call") {
            if (processToolCall(part, accumulator)) {
                hasPendingToolResults = true;
            }
        }
    }
    flushAccumulator(accumulator, result);
}
/**
 * Converts thread messages to generic LLM messages.
 * This format can then be easily converted to provider-specific formats.
 */
export function toGenericMessages(messages) {
    const result = [];
    for (const message of messages) {
        switch (message.role) {
            case "system":
                convertSystemMessage(message, result);
                break;
            case "user":
                convertUserMessage(message, result);
                break;
            case "assistant":
                convertAssistantMessage(message, result);
                break;
        }
    }
    return result;
}
//# sourceMappingURL=toGenericMessages.js.map