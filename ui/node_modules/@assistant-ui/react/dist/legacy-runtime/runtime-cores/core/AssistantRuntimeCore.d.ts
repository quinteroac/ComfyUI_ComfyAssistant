import { ComponentType } from "react";
import type { ModelContextProvider } from "../../../model-context/ModelContextTypes.js";
import type { Unsubscribe } from "../../../types/Unsubscribe.js";
import { ThreadListRuntimeCore } from "./ThreadListRuntimeCore.js";
export type AssistantRuntimeCore = {
    readonly threads: ThreadListRuntimeCore;
    registerModelContextProvider: (provider: ModelContextProvider) => Unsubscribe;
    getModelContextProvider: () => ModelContextProvider;
    /**
     * EXPERIMENTAL: A component that is rendered inside the AssistantRuntimeProvider.
     *
     * Note: This field is expected to never change.
     * To update the component, use a zustand store.
     */
    readonly RenderComponent?: ComponentType | undefined;
};
//# sourceMappingURL=AssistantRuntimeCore.d.ts.map