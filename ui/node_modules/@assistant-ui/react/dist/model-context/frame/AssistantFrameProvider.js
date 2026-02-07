import { z } from "zod";
import { FRAME_MESSAGE_CHANNEL, } from "./AssistantFrameTypes.js";
/**
 * Converts tools to JSON Schema format for serialization
 */
const serializeTool = (tool) => ({
    ...(tool.description && { description: tool.description }),
    parameters: tool.parameters instanceof z.ZodType
        ? (z.toJSONSchema?.(tool.parameters) ?? tool.parameters)
        : tool.parameters,
    ...(tool.disabled !== undefined && { disabled: tool.disabled }),
    ...(tool.type && { type: tool.type }),
});
/**
 * Serializes a ModelContext for transmission across iframe boundary
 */
const serializeModelContext = (context) => ({
    ...(context.system !== undefined && { system: context.system }),
    ...(context.tools && {
        tools: Object.fromEntries(Object.entries(context.tools).map(([name, tool]) => [
            name,
            serializeTool(tool),
        ])),
    }),
});
/**
 * AssistantFrameProvider - Runs inside an iframe and provides ModelContextProviders
 * to the parent window's AssistantFrameHost.
 *
 * Usage example:
 * ```typescript
 * // Inside the iframe
 * // Add model context providers
 * const registry = new ModelContextRegistry();
 * AssistantFrameProvider.addModelContextProvider(registry);
 *
 * // Add tools to registry
 * registry.addTool({
 *   toolName: "search",
 *   description: "Search the web",
 *   parameters: z.object({ query: z.string() }),
 *   execute: async (args) => {
 *     // Tool implementation runs in iframe
 *     return { results: ["..."] };
 *   }
 * });
 * ```
 */
export class AssistantFrameProvider {
    static _instance = null;
    _providers = new Set();
    _providerUnsubscribes = new Map();
    _targetOrigin;
    constructor(targetOrigin = "*") {
        this._targetOrigin = targetOrigin;
        this.handleMessage = this.handleMessage.bind(this);
        window.addEventListener("message", this.handleMessage);
        // Send initial update on initialization
        setTimeout(() => this.broadcastUpdate(), 0);
    }
    static getInstance(targetOrigin) {
        if (!AssistantFrameProvider._instance) {
            AssistantFrameProvider._instance = new AssistantFrameProvider(targetOrigin);
        }
        return AssistantFrameProvider._instance;
    }
    handleMessage(event) {
        // Security: Validate origin if specified
        if (this._targetOrigin !== "*" && event.origin !== this._targetOrigin)
            return;
        if (event.data?.channel !== FRAME_MESSAGE_CHANNEL)
            return;
        const message = event.data.message;
        switch (message.type) {
            case "model-context-request":
                // Respond with current context
                this.sendMessage(event, {
                    type: "model-context-update",
                    context: serializeModelContext(this.getModelContext()),
                });
                break;
            case "tool-call":
                this.handleToolCall(message, event);
                break;
        }
    }
    async handleToolCall(message, event) {
        const tool = this.getModelContext().tools?.[message.toolName];
        let result;
        let error;
        if (!tool) {
            error = `Tool "${message.toolName}" not found`;
        }
        else {
            try {
                result = tool.execute
                    ? await tool.execute(message.args, {
                        toolCallId: message.id,
                        abortSignal: new AbortController().signal,
                        human: async () => {
                            throw new Error("Tool human input is not supported in frame context");
                        },
                    })
                    : undefined;
            }
            catch (e) {
                error = e instanceof Error ? e.message : String(e);
            }
        }
        this.sendMessage(event, {
            type: "tool-result",
            id: message.id,
            ...(error ? { error } : { result }),
        });
    }
    sendMessage(event, message) {
        event.source?.postMessage({ channel: FRAME_MESSAGE_CHANNEL, message }, { targetOrigin: event.origin });
    }
    getModelContext() {
        const contexts = Array.from(this._providers).map((p) => p.getModelContext());
        return contexts.reduce((merged, context) => ({
            system: context.system
                ? merged.system
                    ? `${merged.system}\n\n${context.system}`
                    : context.system
                : merged.system,
            tools: { ...(merged.tools || {}), ...(context.tools || {}) },
        }), {});
    }
    broadcastUpdate() {
        // Always broadcast to parent window
        if (window.parent && window.parent !== window) {
            const updateMessage = {
                type: "model-context-update",
                context: serializeModelContext(this.getModelContext()),
            };
            window.parent.postMessage({ channel: FRAME_MESSAGE_CHANNEL, message: updateMessage }, this._targetOrigin);
        }
    }
    static addModelContextProvider(provider, targetOrigin) {
        const instance = AssistantFrameProvider.getInstance(targetOrigin);
        instance._providers.add(provider);
        const unsubscribe = provider.subscribe?.(() => instance.broadcastUpdate());
        if (unsubscribe) {
            instance._providerUnsubscribes.set(provider, unsubscribe);
        }
        instance.broadcastUpdate();
        return () => {
            instance._providers.delete(provider);
            instance._providerUnsubscribes.get(provider)?.();
            instance._providerUnsubscribes.delete(provider);
            instance.broadcastUpdate();
        };
    }
    static dispose() {
        if (AssistantFrameProvider._instance) {
            const instance = AssistantFrameProvider._instance;
            window.removeEventListener("message", instance.handleMessage);
            // Unsubscribe from all providers
            instance._providerUnsubscribes.forEach((unsubscribe) => unsubscribe?.());
            instance._providerUnsubscribes.clear();
            instance._providers.clear();
            AssistantFrameProvider._instance = null;
        }
    }
}
//# sourceMappingURL=AssistantFrameProvider.js.map