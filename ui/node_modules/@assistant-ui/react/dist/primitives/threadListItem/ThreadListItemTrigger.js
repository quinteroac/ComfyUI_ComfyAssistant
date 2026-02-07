"use client";
import { createActionButton, } from "../../utils/createActionButton.js";
import { useAui } from "@assistant-ui/store";
import { useCallback } from "react";
const useThreadListItemTrigger = () => {
    const aui = useAui();
    return useCallback(() => {
        aui.threadListItem().switchTo();
    }, [aui]);
};
export const ThreadListItemPrimitiveTrigger = createActionButton("ThreadListItemPrimitive.Trigger", useThreadListItemTrigger);
//# sourceMappingURL=ThreadListItemTrigger.js.map