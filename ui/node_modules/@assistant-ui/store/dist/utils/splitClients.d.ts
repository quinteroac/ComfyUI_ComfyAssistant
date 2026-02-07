import { DerivedElement } from "../Derived.js";
import type { AssistantClient, ClientElement, ClientNames } from "../types/client.js";
import type { useAui } from "../useAui.js";
export type RootClients = Partial<Record<ClientNames, ClientElement<ClientNames>>>;
export type DerivedClients = Partial<Record<ClientNames, DerivedElement<ClientNames>>>;
export declare const tapSplitClients: (clients: useAui.Props, baseClient: AssistantClient) => {
    rootClients: Partial<Record<"ERROR: No clients were defined", ClientElement<"ERROR: No clients were defined">>>;
    derivedClients: Partial<Record<"ERROR: No clients were defined", DerivedElement<"ERROR: No clients were defined">>>;
};
//# sourceMappingURL=splitClients.d.ts.map