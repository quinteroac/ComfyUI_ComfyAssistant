import { ChatModelRunOptions, ChatModelRunResult } from "../../local/index.js";
import { ExportedMessageRepository, ExportedMessageRepositoryItem } from "../../utils/MessageRepository.js";
import { MessageFormatAdapter, MessageFormatItem, MessageFormatRepository } from "./MessageFormatAdapter.js";
export type GenericThreadHistoryAdapter<TMessage> = {
    load(): Promise<MessageFormatRepository<TMessage>>;
    append(item: MessageFormatItem<TMessage>): Promise<void>;
};
export type ThreadHistoryAdapter = {
    load(): Promise<ExportedMessageRepository & {
        unstable_resume?: boolean;
    }>;
    resume?(options: ChatModelRunOptions): AsyncGenerator<ChatModelRunResult, void, unknown>;
    append(item: ExportedMessageRepositoryItem): Promise<void>;
    withFormat?<TMessage, TStorageFormat>(formatAdapter: MessageFormatAdapter<TMessage, TStorageFormat>): GenericThreadHistoryAdapter<TMessage>;
};
//# sourceMappingURL=ThreadHistoryAdapter.d.ts.map