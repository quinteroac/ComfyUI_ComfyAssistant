import { Tool, type ToolJSONSchema } from "assistant-stream";
/**
 * @deprecated Use `toToolsJSONSchema` from `assistant-stream` instead.
 */
export declare function toAISDKTools(tools: Record<string, Tool>): Record<string, ToolJSONSchema>;
/**
 * @deprecated Use `toToolsJSONSchema` from `assistant-stream` instead, which includes filtering by default.
 */
export declare function getEnabledTools(tools: Record<string, Tool>): Record<string, Tool>;
export declare function createRequestHeaders(headersValue: Record<string, string> | Headers | (() => Promise<Record<string, string> | Headers>)): Promise<Headers>;
//# sourceMappingURL=utils.d.ts.map