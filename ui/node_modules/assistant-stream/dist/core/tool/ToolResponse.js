const TOOL_RESPONSE_SYMBOL = Symbol.for("aui.tool-response");
export class ToolResponse {
    get [TOOL_RESPONSE_SYMBOL]() {
        return true;
    }
    artifact;
    result;
    isError;
    constructor(options) {
        if (options.artifact !== undefined) {
            this.artifact = options.artifact;
        }
        this.result = options.result;
        this.isError = options.isError ?? false;
    }
    static [Symbol.hasInstance](obj) {
        return (typeof obj === "object" && obj !== null && TOOL_RESPONSE_SYMBOL in obj);
    }
    static toResponse(result) {
        if (result instanceof ToolResponse) {
            return result;
        }
        return new ToolResponse({
            result: result === undefined ? "<no result>" : result,
        });
    }
}
//# sourceMappingURL=ToolResponse.js.map