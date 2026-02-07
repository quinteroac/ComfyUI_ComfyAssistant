import { jsx as _jsx } from "react/jsx-runtime";
import { memo } from "react";
const areChildrenEqual = (prev, next) => {
    if (typeof prev === "string")
        return prev === next;
    return JSON.stringify(prev) === JSON.stringify(next);
};
export const areNodesEqual = (prev, next) => {
    if (!prev || !next)
        return false;
    const excludeMetadata = (props) => {
        const { position, data, ...rest } = props || {};
        return rest;
    };
    return (JSON.stringify(excludeMetadata(prev.properties)) ===
        JSON.stringify(excludeMetadata(next.properties)) &&
        areChildrenEqual(prev.children, next.children));
};
export const memoCompareNodes = (prev, next) => {
    return areNodesEqual(prev.node, next.node);
};
export const memoizeMarkdownComponents = (components = {}) => {
    return Object.fromEntries(Object.entries(components ?? {}).map(([key, value]) => {
        if (!value)
            return [key, value];
        const Component = value;
        const WithoutNode = ({ node, ...props }) => {
            return _jsx(Component, { ...props });
        };
        return [key, memo(WithoutNode, memoCompareNodes)];
    }));
};
//# sourceMappingURL=memoization.js.map