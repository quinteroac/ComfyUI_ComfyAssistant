import { ToolResponse } from "assistant-stream";
export class MessagePartRuntimeImpl {
    contentBinding;
    messageApi;
    threadApi;
    get path() {
        return this.contentBinding.path;
    }
    constructor(contentBinding, messageApi, threadApi) {
        this.contentBinding = contentBinding;
        this.messageApi = messageApi;
        this.threadApi = threadApi;
        this.__internal_bindMethods();
    }
    __internal_bindMethods() {
        this.addToolResult = this.addToolResult.bind(this);
        this.resumeToolCall = this.resumeToolCall.bind(this);
        this.getState = this.getState.bind(this);
        this.subscribe = this.subscribe.bind(this);
    }
    getState() {
        return this.contentBinding.getState();
    }
    addToolResult(result) {
        const state = this.contentBinding.getState();
        if (!state)
            throw new Error("Message part is not available");
        if (state.type !== "tool-call")
            throw new Error("Tried to add tool result to non-tool message part");
        if (!this.messageApi)
            throw new Error("Message API is not available. This is likely a bug in assistant-ui.");
        if (!this.threadApi)
            throw new Error("Thread API is not available");
        const message = this.messageApi.getState();
        if (!message)
            throw new Error("Message is not available");
        const toolName = state.toolName;
        const toolCallId = state.toolCallId;
        const response = ToolResponse.toResponse(result);
        this.threadApi.getState().addToolResult({
            messageId: message.id,
            toolName,
            toolCallId,
            result: response.result,
            artifact: response.artifact,
            isError: response.isError,
        });
    }
    resumeToolCall(payload) {
        const state = this.contentBinding.getState();
        if (!state)
            throw new Error("Message part is not available");
        if (state.type !== "tool-call")
            throw new Error("Tried to resume tool call on non-tool message part");
        if (!this.threadApi)
            throw new Error("Thread API is not available");
        const toolCallId = state.toolCallId;
        this.threadApi.getState().resumeToolCall({
            toolCallId,
            payload,
        });
    }
    subscribe(callback) {
        return this.contentBinding.subscribe(callback);
    }
}
//# sourceMappingURL=MessagePartRuntime.js.map