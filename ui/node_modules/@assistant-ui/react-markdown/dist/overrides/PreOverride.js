"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, useContext, memo, } from "react";
import { memoCompareNodes } from "../memoization.js";
export const PreContext = createContext(null);
export const useIsMarkdownCodeBlock = () => {
    return useContext(PreContext) !== null;
};
const PreOverrideImpl = ({ children, ...rest }) => {
    return _jsx(PreContext.Provider, { value: rest, children: children });
};
export const PreOverride = memo(PreOverrideImpl, memoCompareNodes);
//# sourceMappingURL=PreOverride.js.map