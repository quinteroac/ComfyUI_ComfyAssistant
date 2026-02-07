import { resource, withKey, } from "@assistant-ui/tap";
export const wrapperResource = (fn) => {
    const res = resource(fn);
    return (props) => {
        const el = res(props);
        if (props.key === undefined)
            return el;
        return withKey(props.key, el);
    };
};
//# sourceMappingURL=wrapperResource.js.map