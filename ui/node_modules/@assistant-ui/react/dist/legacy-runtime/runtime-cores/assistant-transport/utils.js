import { toToolsJSONSchema } from "assistant-stream";
/**
 * @deprecated Use `toToolsJSONSchema` from `assistant-stream` instead.
 */
export function toAISDKTools(tools) {
    return toToolsJSONSchema(tools, { filter: () => true });
}
/**
 * @deprecated Use `toToolsJSONSchema` from `assistant-stream` instead, which includes filtering by default.
 */
export function getEnabledTools(tools) {
    return Object.fromEntries(Object.entries(tools).filter(([, tool]) => !tool.disabled && tool.type !== "backend"));
}
export async function createRequestHeaders(headersValue) {
    const resolvedHeaders = typeof headersValue === "function" ? await headersValue() : headersValue;
    const headers = new Headers(resolvedHeaders);
    headers.set("Content-Type", "application/json");
    return headers;
}
//# sourceMappingURL=utils.js.map