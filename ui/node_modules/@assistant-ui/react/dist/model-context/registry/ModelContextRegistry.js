import { mergeModelContexts, } from "../../model-context/ModelContextTypes.js";
export class ModelContextRegistry {
    _tools = new Map();
    _instructions = new Map();
    _providers = new Map();
    _subscribers = new Set();
    _providerUnsubscribes = new Map();
    getModelContext() {
        // Merge instructions
        const instructions = Array.from(this._instructions.values()).filter(Boolean);
        const system = instructions.length > 0 ? instructions.join("\n\n") : undefined;
        // Collect tools
        const tools = {};
        for (const toolProps of this._tools.values()) {
            const { toolName, render, ...tool } = toolProps;
            tools[toolName] = tool;
        }
        // Merge provider contexts
        const providerContexts = mergeModelContexts(new Set(this._providers.values()));
        // Combine everything
        const context = {
            system,
            tools: Object.keys(tools).length > 0 ? tools : undefined,
        };
        // Merge with provider contexts
        if (providerContexts.system) {
            context.system = context.system
                ? `${context.system}\n\n${providerContexts.system}`
                : providerContexts.system;
        }
        if (providerContexts.tools) {
            context.tools = { ...(context.tools || {}), ...providerContexts.tools };
        }
        if (providerContexts.callSettings) {
            context.callSettings = providerContexts.callSettings;
        }
        if (providerContexts.config) {
            context.config = providerContexts.config;
        }
        return context;
    }
    subscribe(callback) {
        this._subscribers.add(callback);
        return () => this._subscribers.delete(callback);
    }
    notifySubscribers() {
        for (const callback of this._subscribers) {
            callback();
        }
    }
    addTool(tool) {
        const id = Symbol();
        this._tools.set(id, tool);
        this.notifySubscribers();
        return {
            update: (newTool) => {
                if (this._tools.has(id)) {
                    this._tools.set(id, newTool);
                    this.notifySubscribers();
                }
            },
            remove: () => {
                this._tools.delete(id);
                this.notifySubscribers();
            },
        };
    }
    addInstruction(config) {
        const id = Symbol();
        const instruction = typeof config === "string" ? config : config.instruction;
        const disabled = typeof config === "object" ? config.disabled : false;
        if (!disabled) {
            this._instructions.set(id, instruction);
            this.notifySubscribers();
        }
        return {
            update: (newConfig) => {
                const newInstruction = typeof newConfig === "string" ? newConfig : newConfig.instruction;
                const newDisabled = typeof newConfig === "object" ? newConfig.disabled : false;
                if (newDisabled) {
                    this._instructions.delete(id);
                }
                else {
                    this._instructions.set(id, newInstruction);
                }
                this.notifySubscribers();
            },
            remove: () => {
                this._instructions.delete(id);
                this.notifySubscribers();
            },
        };
    }
    addProvider(provider) {
        const id = Symbol();
        this._providers.set(id, provider);
        // Subscribe to provider changes
        const unsubscribe = provider.subscribe?.(() => {
            this.notifySubscribers();
        });
        this._providerUnsubscribes.set(id, unsubscribe);
        this.notifySubscribers();
        return {
            remove: () => {
                this._providers.delete(id);
                const unsubscribe = this._providerUnsubscribes.get(id);
                unsubscribe?.();
                this._providerUnsubscribes.delete(id);
                this.notifySubscribers();
            },
        };
    }
}
//# sourceMappingURL=ModelContextRegistry.js.map