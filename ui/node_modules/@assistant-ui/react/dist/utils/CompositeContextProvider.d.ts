import { type ModelContextProvider } from "../model-context/ModelContextTypes.js";
export declare class CompositeContextProvider implements ModelContextProvider {
    private _providers;
    getModelContext(): import("..").ModelContext;
    registerModelContextProvider(provider: ModelContextProvider): () => void;
    private _subscribers;
    notifySubscribers(): void;
    subscribe(callback: () => void): () => boolean;
}
//# sourceMappingURL=CompositeContextProvider.d.ts.map