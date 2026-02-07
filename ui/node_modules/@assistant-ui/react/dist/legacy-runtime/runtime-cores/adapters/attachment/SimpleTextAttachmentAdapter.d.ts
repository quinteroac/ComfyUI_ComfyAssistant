import { CompleteAttachment, PendingAttachment } from "../../../../types/AttachmentTypes.js";
import { AttachmentAdapter } from "./AttachmentAdapter.js";
export declare class SimpleTextAttachmentAdapter implements AttachmentAdapter {
    accept: string;
    add(state: {
        file: File;
    }): Promise<PendingAttachment>;
    send(attachment: PendingAttachment): Promise<CompleteAttachment>;
    remove(): Promise<void>;
}
//# sourceMappingURL=SimpleTextAttachmentAdapter.d.ts.map