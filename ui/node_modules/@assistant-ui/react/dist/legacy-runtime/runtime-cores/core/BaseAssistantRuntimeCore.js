import { CompositeContextProvider } from "../../../utils/CompositeContextProvider.js";
export class BaseAssistantRuntimeCore {
    _contextProvider = new CompositeContextProvider();
    registerModelContextProvider(provider) {
        return this._contextProvider.registerModelContextProvider(provider);
    }
    getModelContextProvider() {
        return this._contextProvider;
    }
}
//# sourceMappingURL=BaseAssistantRuntimeCore.js.map