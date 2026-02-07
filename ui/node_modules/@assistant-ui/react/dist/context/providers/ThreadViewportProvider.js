"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { useEffect, useState } from "react";
import { makeThreadViewportStore, } from "../stores/ThreadViewport.js";
import { ThreadViewportContext, useThreadViewportStore, } from "../react/ThreadViewportContext.js";
import { writableStore } from "../ReadonlyStore.js";
const useThreadViewportStoreValue = (options) => {
    const outerViewport = useThreadViewportStore({ optional: true });
    const [store] = useState(() => makeThreadViewportStore(options));
    // Forward scrollToBottom from outer viewport to inner viewport
    useEffect(() => {
        return outerViewport?.getState().onScrollToBottom(() => {
            store.getState().scrollToBottom();
        });
    }, [outerViewport, store]);
    useEffect(() => {
        if (!outerViewport)
            return;
        return store.subscribe((state) => {
            if (outerViewport.getState().isAtBottom !== state.isAtBottom) {
                writableStore(outerViewport).setState({ isAtBottom: state.isAtBottom });
            }
        });
    }, [store, outerViewport]);
    // Sync options to store when they change
    useEffect(() => {
        const nextState = {
            turnAnchor: options.turnAnchor ?? "bottom",
        };
        const currentState = store.getState();
        if (currentState.turnAnchor !== nextState.turnAnchor) {
            writableStore(store).setState(nextState);
        }
    }, [store, options.turnAnchor]);
    return store;
};
export const ThreadPrimitiveViewportProvider = ({ children, options = {} }) => {
    const useThreadViewport = useThreadViewportStoreValue(options);
    const [context] = useState(() => {
        return {
            useThreadViewport,
        };
    });
    return (_jsx(ThreadViewportContext.Provider, { value: context, children: children }));
};
//# sourceMappingURL=ThreadViewportProvider.js.map