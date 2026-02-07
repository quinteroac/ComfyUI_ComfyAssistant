"use client";
import { useCallback, useEffect, useState } from "react";
import { create } from "zustand";
export const useInlineRender = (toolUI) => {
    const [useToolUIStore] = useState(() => create(() => ({
        toolUI,
    })));
    useEffect(() => {
        useToolUIStore.setState({ toolUI });
    }, [toolUI, useToolUIStore]);
    return useCallback(function ToolUI(args) {
        const store = useToolUIStore();
        return store.toolUI(args);
    }, [useToolUIStore]);
};
//# sourceMappingURL=useInlineRender.js.map