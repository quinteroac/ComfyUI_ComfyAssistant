import { PendingAttachment, CompleteAttachment } from "../../../../types/AttachmentTypes.js";
import { AttachmentAdapter } from "./AttachmentAdapter.js";
export declare class SimpleImageAttachmentAdapter implements AttachmentAdapter {
    accept: string;
    add(state: {
        file: File;
    }): Promise<PendingAttachment>;
    send(attachment: PendingAttachment): Promise<CompleteAttachment>;
    remove(): Promise<void>;
}
//# sourceMappingURL=SimpleImageAttachmentAdapter.d.ts.map