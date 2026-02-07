import { mergeModelContexts, } from "../model-context/ModelContextTypes.js";
export class CompositeContextProvider {
    _providers = new Set();
    getModelContext() {
        return mergeModelContexts(this._providers);
    }
    registerModelContextProvider(provider) {
        this._providers.add(provider);
        const unsubscribe = provider.subscribe?.(() => {
            this.notifySubscribers();
        });
        this.notifySubscribers();
        return () => {
            this._providers.delete(provider);
            unsubscribe?.();
            this.notifySubscribers();
        };
    }
    _subscribers = new Set();
    notifySubscribers() {
        for (const callback of this._subscribers)
            callback();
    }
    subscribe(callback) {
        this._subscribers.add(callback);
        return () => this._subscribers.delete(callback);
    }
}
//# sourceMappingURL=CompositeContextProvider.js.map