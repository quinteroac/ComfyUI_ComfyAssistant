import { AssistantStream } from "../AssistantStream.js";
import { ToolResponseLike } from "../tool/ToolResponse.js";
import { ReadonlyJSONValue } from "../../utils/json/json-value.js";
import { UnderlyingReadable } from "../utils/stream/UnderlyingReadable.js";
import { TextStreamController } from "./text.js";
export type ToolCallStreamController = {
    argsText: TextStreamController;
    setResponse(response: ToolResponseLike<ReadonlyJSONValue>): void;
    close(): void;
};
export declare const createToolCallStream: (readable: UnderlyingReadable<ToolCallStreamController>) => AssistantStream;
export declare const createToolCallStreamController: () => readonly [AssistantStream, ToolCallStreamController];
//# sourceMappingURL=tool-call.d.ts.map