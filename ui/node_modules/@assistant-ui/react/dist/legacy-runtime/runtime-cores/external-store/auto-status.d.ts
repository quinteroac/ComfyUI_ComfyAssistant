import { ReadonlyJSONValue } from "assistant-stream/utils";
import { MessageStatus } from "../../../types/index.js";
export declare const isAutoStatus: (status: MessageStatus) => boolean;
export declare const getAutoStatus: (isLast: boolean, isRunning: boolean, hasInterruptedToolCalls: boolean, hasPendingToolCalls: boolean, error?: ReadonlyJSONValue) => MessageStatus;
//# sourceMappingURL=auto-status.d.ts.map