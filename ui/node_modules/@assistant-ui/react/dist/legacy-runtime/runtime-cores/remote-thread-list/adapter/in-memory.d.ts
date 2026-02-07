import { AssistantStream } from "assistant-stream";
import { RemoteThreadInitializeResponse, RemoteThreadListAdapter, RemoteThreadListResponse, RemoteThreadMetadata } from "../types.js";
export declare class InMemoryThreadListAdapter implements RemoteThreadListAdapter {
    list(): Promise<RemoteThreadListResponse>;
    rename(): Promise<void>;
    archive(): Promise<void>;
    unarchive(): Promise<void>;
    delete(): Promise<void>;
    initialize(threadId: string): Promise<RemoteThreadInitializeResponse>;
    generateTitle(): Promise<AssistantStream>;
    fetch(_threadId: string): Promise<RemoteThreadMetadata>;
}
//# sourceMappingURL=in-memory.d.ts.map