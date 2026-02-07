import { fnSymbol } from "./callResourceFn.js";
export function resource(fn) {
    const type = (props) => {
        return {
            type,
            props: props,
        };
    };
    type[fnSymbol] = fn;
    return type;
}
//# sourceMappingURL=resource.js.map