import { AssistantCloudThreadMessages } from "./AssistantCloudThreadMessages.js";
export class AssistantCloudThreads {
    cloud;
    messages;
    constructor(cloud) {
        this.cloud = cloud;
        this.messages = new AssistantCloudThreadMessages(cloud);
    }
    async list(query) {
        return this.cloud.makeRequest("/threads", { query });
    }
    async get(threadId) {
        return this.cloud.makeRequest(`/threads/${encodeURIComponent(threadId)}`);
    }
    async create(body) {
        return this.cloud.makeRequest("/threads", { method: "POST", body });
    }
    async update(threadId, body) {
        return this.cloud.makeRequest(`/threads/${encodeURIComponent(threadId)}`, {
            method: "PUT",
            body,
        });
    }
    async delete(threadId) {
        return this.cloud.makeRequest(`/threads/${encodeURIComponent(threadId)}`, {
            method: "DELETE",
        });
    }
}
//# sourceMappingURL=AssistantCloudThreads.js.map