"use client";
import { create } from "zustand";
const createSizeRegistry = (onChange) => {
    const entries = new Map();
    const recalculate = () => {
        let total = 0;
        for (const height of entries.values()) {
            total += height;
        }
        onChange(total);
    };
    return {
        register: () => {
            const id = Symbol();
            entries.set(id, 0);
            return {
                setHeight: (height) => {
                    if (entries.get(id) !== height) {
                        entries.set(id, height);
                        recalculate();
                    }
                },
                unregister: () => {
                    entries.delete(id);
                    recalculate();
                },
            };
        },
    };
};
export const makeThreadViewportStore = (options = {}) => {
    const scrollToBottomListeners = new Set();
    const viewportRegistry = createSizeRegistry((total) => {
        store.setState({
            height: {
                ...store.getState().height,
                viewport: total,
            },
        });
    });
    const insetRegistry = createSizeRegistry((total) => {
        store.setState({
            height: {
                ...store.getState().height,
                inset: total,
            },
        });
    });
    const userMessageRegistry = createSizeRegistry((total) => {
        store.setState({
            height: {
                ...store.getState().height,
                userMessage: total,
            },
        });
    });
    const store = create(() => ({
        isAtBottom: true,
        scrollToBottom: ({ behavior = "auto" } = {}) => {
            for (const listener of scrollToBottomListeners) {
                listener({ behavior });
            }
        },
        onScrollToBottom: (callback) => {
            scrollToBottomListeners.add(callback);
            return () => {
                scrollToBottomListeners.delete(callback);
            };
        },
        turnAnchor: options.turnAnchor ?? "bottom",
        height: {
            viewport: 0,
            inset: 0,
            userMessage: 0,
        },
        registerViewport: viewportRegistry.register,
        registerContentInset: insetRegistry.register,
        registerUserMessageHeight: userMessageRegistry.register,
    }));
    return store;
};
//# sourceMappingURL=ThreadViewport.js.map