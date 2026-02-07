export class InMemoryThreadListAdapter {
    list() {
        return Promise.resolve({
            threads: [],
        });
    }
    rename() {
        return Promise.resolve();
    }
    archive() {
        return Promise.resolve();
    }
    unarchive() {
        return Promise.resolve();
    }
    delete() {
        return Promise.resolve();
    }
    initialize(threadId) {
        return Promise.resolve({ remoteId: threadId, externalId: undefined });
    }
    generateTitle() {
        return Promise.resolve(new ReadableStream());
    }
    fetch(_threadId) {
        return Promise.reject(new Error("Thread not found"));
    }
}
//# sourceMappingURL=in-memory.js.map