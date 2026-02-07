import { ResourceElement } from "@assistant-ui/tap";
import type { AssistantClient, ClientNames, AssistantClientAccessor, ClientMeta } from "./types/client.js";
/**
 * Creates a derived client field that references a client from a parent scope.
 * The get callback always calls the most recent version (useEffectEvent pattern).
 *
 * IMPORTANT: The `get` callback must return a client that was created via
 * `tapClientResource` (or `tapClientLookup`/`tapClientList` which use it internally).
 * This is required for event scoping to work correctly.
 *
 * @example
 * ```typescript
 * const aui = useAui({
 *   message: Derived({
 *     source: "thread",
 *     query: { index: 0 },
 *     get: (aui) => aui.thread().message({ index: 0 }),
 *   }),
 * });
 * ```
 */
export declare const Derived: <K extends ClientNames>(props: Derived.Props<K>) => ResourceElement<null, Derived.Props<K>>;
export type DerivedElement<K extends ClientNames> = ResourceElement<null, Derived.Props<K>>;
export declare namespace Derived {
    /**
     * Props passed to a derived client resource element.
     */
    type Props<K extends ClientNames> = {
        get: (client: AssistantClient) => ReturnType<AssistantClientAccessor<K>>;
    } & (ClientMeta<K> | {
        getMeta: (client: AssistantClient) => ClientMeta<K>;
    });
}
//# sourceMappingURL=Derived.d.ts.map