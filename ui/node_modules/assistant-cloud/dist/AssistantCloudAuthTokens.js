export class AssistantCloudAuthTokens {
    cloud;
    constructor(cloud) {
        this.cloud = cloud;
    }
    async create() {
        return this.cloud.makeRequest("/auth/tokens", { method: "POST" });
    }
}
//# sourceMappingURL=AssistantCloudAuthTokens.js.map