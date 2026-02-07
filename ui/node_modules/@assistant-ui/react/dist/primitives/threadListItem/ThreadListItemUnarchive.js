"use client";
import { createActionButton, } from "../../utils/createActionButton.js";
import { useAui } from "@assistant-ui/store";
import { useCallback } from "react";
const useThreadListItemUnarchive = () => {
    const aui = useAui();
    return useCallback(() => {
        aui.threadListItem().unarchive();
    }, [aui]);
};
export const ThreadListItemPrimitiveUnarchive = createActionButton("ThreadListItemPrimitive.Unarchive", useThreadListItemUnarchive);
//# sourceMappingURL=ThreadListItemUnarchive.js.map