import { type ModelContextProvider } from "../../../model-context/ModelContextTypes.js";
import type { Unsubscribe } from "../../../types/Unsubscribe.js";
import type { AssistantRuntimeCore } from "./AssistantRuntimeCore.js";
import { CompositeContextProvider } from "../../../utils/CompositeContextProvider.js";
import { ThreadListRuntimeCore } from "./ThreadListRuntimeCore.js";
export declare abstract class BaseAssistantRuntimeCore implements AssistantRuntimeCore {
    protected readonly _contextProvider: CompositeContextProvider;
    abstract get threads(): ThreadListRuntimeCore;
    registerModelContextProvider(provider: ModelContextProvider): Unsubscribe;
    getModelContextProvider(): ModelContextProvider;
}
//# sourceMappingURL=BaseAssistantRuntimeCore.d.ts.map