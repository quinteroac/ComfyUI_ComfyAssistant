"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { createContext, forwardRef, useContext, useState, } from "react";
import { create } from "zustand";
import { useAui } from "@assistant-ui/store";
import { createContextStoreHook } from "../../context/react/utils/createContextStoreHook.js";
const SmoothContext = createContext(null);
const makeSmoothContext = (initialState) => {
    const useSmoothStatus = create(() => initialState);
    return { useSmoothStatus };
};
export const SmoothContextProvider = ({ children }) => {
    const outer = useSmoothContext({ optional: true });
    const aui = useAui();
    const [context] = useState(() => makeSmoothContext(aui.part().getState().status));
    // do not wrap if there is an outer SmoothContextProvider
    if (outer)
        return children;
    return (_jsx(SmoothContext.Provider, { value: context, children: children }));
};
export const withSmoothContextProvider = (Component) => {
    const Wrapped = forwardRef((props, ref) => {
        return (_jsx(SmoothContextProvider, { children: _jsx(Component, { ...props, ref: ref }) }));
    });
    Wrapped.displayName = Component.displayName;
    return Wrapped;
};
function useSmoothContext(options) {
    const context = useContext(SmoothContext);
    if (!options?.optional && !context)
        throw new Error("This component must be used within a SmoothContextProvider.");
    return context;
}
export const { useSmoothStatus, useSmoothStatusStore } = createContextStoreHook(useSmoothContext, "useSmoothStatus");
//# sourceMappingURL=SmoothContext.js.map