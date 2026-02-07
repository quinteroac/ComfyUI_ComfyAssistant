import type { AssistantToolProps } from "../../model-context/useAssistantTool.js";
import type { AssistantInstructionsConfig } from "../../model-context/useAssistantInstructions.js";
export interface ModelContextRegistryToolHandle<TArgs extends Record<string, unknown> = any, TResult = any> {
    update(tool: AssistantToolProps<TArgs, TResult>): void;
    remove(): void;
}
export interface ModelContextRegistryInstructionHandle {
    update(config: string | AssistantInstructionsConfig): void;
    remove(): void;
}
export interface ModelContextRegistryProviderHandle {
    remove(): void;
}
//# sourceMappingURL=ModelContextRegistryHandles.d.ts.map