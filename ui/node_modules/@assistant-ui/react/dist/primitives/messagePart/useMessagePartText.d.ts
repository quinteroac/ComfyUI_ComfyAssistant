import { TextMessagePart, ReasoningMessagePart } from "../../types/index.js";
export declare const useMessagePartText: () => (TextMessagePart & {
    readonly status: import("../..").MessagePartStatus | import("../..").ToolCallMessagePartStatus;
}) | (ReasoningMessagePart & {
    readonly status: import("../..").MessagePartStatus | import("../..").ToolCallMessagePartStatus;
});
//# sourceMappingURL=useMessagePartText.d.ts.map