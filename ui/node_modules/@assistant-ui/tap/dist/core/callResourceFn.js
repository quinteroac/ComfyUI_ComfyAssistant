/**
 * Renders a resource with the given props.
 * @internal This is for internal use only.
 */
export function callResourceFn(resource, props) {
    const fn = resource[fnSymbol];
    if (!fn) {
        throw new Error("ResourceElement.type is not a valid Resource");
    }
    return fn(props);
}
/**
 * Symbol used to store the ResourceFn in the Resource constructor.
 * @internal This is for internal use only.
 */
export const fnSymbol = Symbol("fnSymbol");
//# sourceMappingURL=callResourceFn.js.map