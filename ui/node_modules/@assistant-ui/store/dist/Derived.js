import { resource } from "@assistant-ui/tap";
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
export const Derived = resource((_config) => {
    return null;
});
//# sourceMappingURL=Derived.js.map