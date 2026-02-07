"use client";
import { createActionButton, } from "../../utils/createActionButton.js";
import { useCallback } from "react";
import { useAui } from "@assistant-ui/store";
const useAttachmentRemove = () => {
    const aui = useAui();
    const handleRemoveAttachment = useCallback(() => {
        aui.attachment().remove();
    }, [aui]);
    return handleRemoveAttachment;
};
export const AttachmentPrimitiveRemove = createActionButton("AttachmentPrimitive.Remove", useAttachmentRemove);
//# sourceMappingURL=AttachmentRemove.js.map