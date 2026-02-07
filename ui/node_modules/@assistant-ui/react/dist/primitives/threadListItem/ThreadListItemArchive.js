"use client";
import { createActionButton, } from "../../utils/createActionButton.js";
import { useAui } from "@assistant-ui/store";
import { useCallback } from "react";
const useThreadListItemArchive = () => {
    const aui = useAui();
    return useCallback(() => {
        aui.threadListItem().archive();
    }, [aui]);
};
export const ThreadListItemPrimitiveArchive = createActionButton("ThreadListItemPrimitive.Archive", useThreadListItemArchive);
//# sourceMappingURL=ThreadListItemArchive.js.map