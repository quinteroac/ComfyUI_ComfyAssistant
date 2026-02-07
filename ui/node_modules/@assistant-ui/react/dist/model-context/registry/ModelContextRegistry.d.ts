import { ModelContext, ModelContextProvider } from "../../model-context/ModelContextTypes.js";
import { Unsubscribe } from "../../types/Unsubscribe.js";
import { ModelContextRegistryToolHandle, ModelContextRegistryInstructionHandle, ModelContextRegistryProviderHandle } from "./ModelContextRegistryHandles.js";
import type { AssistantToolProps } from "../../model-context/useAssistantTool.js";
import type { AssistantInstructionsConfig } from "../../model-context/useAssistantInstructions.js";
export declare class ModelContextRegistry implements ModelContextProvider {
    private _tools;
    private _instructions;
    private _providers;
    private _subscribers;
    private _providerUnsubscribes;
    getModelContext(): ModelContext;
    subscribe(callback: () => void): Unsubscribe;
    private notifySubscribers;
    addTool<TArgs extends Record<string, unknown>, TResult>(tool: AssistantToolProps<TArgs, TResult>): ModelContextRegistryToolHandle<TArgs, TResult>;
    addInstruction(config: string | AssistantInstructionsConfig): ModelContextRegistryInstructionHandle;
    addProvider(provider: ModelContextProvider): ModelContextRegistryProviderHandle;
}
//# sourceMappingURL=ModelContextRegistry.d.ts.map