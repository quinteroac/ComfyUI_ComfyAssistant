import { AssistantStream } from "../AssistantStream.js";
import { AssistantStreamChunk } from "../AssistantStreamChunk.js";
import { TextStreamController } from "./text.js";
import { ToolCallStreamController } from "./tool-call.js";
import { FilePart, SourcePart } from "../utils/types.js";
import { ReadonlyJSONObject, ReadonlyJSONValue } from "../../utils/json/json-value.js";
import { ToolResponseLike } from "../tool/ToolResponse.js";
type ToolCallPartInit = {
    toolCallId?: string;
    toolName: string;
    argsText?: string;
    args?: ReadonlyJSONObject;
    response?: ToolResponseLike<ReadonlyJSONValue>;
};
export type AssistantStreamController = {
    appendText(textDelta: string): void;
    appendReasoning(reasoningDelta: string): void;
    appendSource(options: SourcePart): void;
    appendFile(options: FilePart): void;
    addTextPart(): TextStreamController;
    addToolCallPart(options: string): ToolCallStreamController;
    addToolCallPart(options: ToolCallPartInit): ToolCallStreamController;
    enqueue(chunk: AssistantStreamChunk): void;
    merge(stream: AssistantStream): void;
    close(): void;
    withParentId(parentId: string): AssistantStreamController;
};
export declare function createAssistantStream(callback: (controller: AssistantStreamController) => PromiseLike<void> | void): AssistantStream;
export declare function createAssistantStreamController(): readonly [AssistantStream, AssistantStreamController];
export declare function createAssistantStreamResponse(callback: (controller: AssistantStreamController) => PromiseLike<void> | void): Response;
export {};
//# sourceMappingURL=assistant-stream.d.ts.map