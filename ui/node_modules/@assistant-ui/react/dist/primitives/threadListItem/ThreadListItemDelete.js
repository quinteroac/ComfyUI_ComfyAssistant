"use client";
import { createActionButton, } from "../../utils/createActionButton.js";
import { useAui } from "@assistant-ui/store";
import { useCallback } from "react";
const useThreadListItemDelete = () => {
    const aui = useAui();
    return useCallback(() => {
        aui.threadListItem().delete();
    }, [aui]);
};
export const ThreadListItemPrimitiveDelete = createActionButton("ThreadListItemPrimitive.Delete", useThreadListItemDelete);
//# sourceMappingURL=ThreadListItemDelete.js.map