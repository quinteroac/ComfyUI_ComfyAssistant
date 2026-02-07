const INTROSPECTION_PROPS = new Set(["$$typeof", "nodeType", "then"]);
/**
 * Handles common proxy introspection properties.
 * Returns the appropriate value for toStringTag, toJSON, and props that should return undefined.
 * Returns `false` if the prop should be handled by the subclass.
 */
export const handleIntrospectionProp = (prop, name) => {
    if (prop === Symbol.toStringTag)
        return name;
    if (typeof prop === "symbol")
        return undefined;
    if (prop === "toJSON")
        return () => name;
    if (INTROSPECTION_PROPS.has(prop))
        return undefined;
    return false;
};
export class BaseProxyHandler {
    getOwnPropertyDescriptor(_, prop) {
        const value = this.get(_, prop);
        if (value === undefined)
            return undefined;
        return {
            value,
            writable: false,
            enumerable: true,
            configurable: false,
        };
    }
    set() {
        return false;
    }
    setPrototypeOf() {
        return false;
    }
    defineProperty() {
        return false;
    }
    deleteProperty() {
        return false;
    }
    preventExtensions() {
        return false;
    }
}
//# sourceMappingURL=BaseProxyHandler.js.map