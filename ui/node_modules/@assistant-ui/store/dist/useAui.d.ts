import type { AssistantClient, ClientNames, ClientElement } from "./types/client.js";
import { DerivedElement } from "./Derived.js";
/**
 * Resource that creates an extended AssistantClient.
 */
export declare const AssistantClientResource: (props: {
    parent: AssistantClient;
    clients: useAui.Props;
}) => import("@assistant-ui/tap").ResourceElement<AssistantClient, {
    parent: AssistantClient;
    clients: useAui.Props;
}>;
export declare namespace useAui {
    type Props = {
        [K in ClientNames]?: ClientElement<K> | DerivedElement<K>;
    };
}
export declare function useAui(): AssistantClient;
export declare function useAui(clients: useAui.Props): AssistantClient;
export declare function useAui(clients: useAui.Props, config: {
    parent: null | AssistantClient;
}): AssistantClient;
//# sourceMappingURL=useAui.d.ts.map