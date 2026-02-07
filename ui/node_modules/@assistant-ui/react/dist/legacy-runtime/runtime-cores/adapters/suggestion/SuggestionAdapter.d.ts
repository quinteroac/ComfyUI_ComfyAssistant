import { ThreadMessage } from "../../../../types/AssistantTypes.js";
import { ThreadSuggestion } from "../../core/index.js";
type SuggestionAdapterGenerateOptions = {
    messages: readonly ThreadMessage[];
};
export type SuggestionAdapter = {
    generate: (options: SuggestionAdapterGenerateOptions) => Promise<readonly ThreadSuggestion[]> | AsyncGenerator<readonly ThreadSuggestion[], void>;
};
export {};
//# sourceMappingURL=SuggestionAdapter.d.ts.map