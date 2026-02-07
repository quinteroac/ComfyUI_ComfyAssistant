function fileMatchesAccept(file, acceptString) {
    // Check if the accept string is "*", which allows any file
    if (acceptString === "*") {
        return true;
    }
    // Split the accept string into an array of allowed types
    const allowedTypes = acceptString
        .split(",")
        .map((type) => type.trim().toLowerCase());
    // Get the file's extension and MIME type
    const fileExtension = `.${file.name.split(".").pop().toLowerCase()}`;
    const fileMimeType = file.type.toLowerCase();
    for (const type of allowedTypes) {
        // Check for file extension match
        if (type.startsWith(".") && type === fileExtension) {
            return true;
        }
        // Check for exact MIME type match
        if (type.includes("/") && type === fileMimeType) {
            return true;
        }
        if (type === "image/*" || type === "video/*" || type === "audio/*") {
            // Check for wildcard MIME type match
            if (type.endsWith("/*")) {
                const generalType = type.split("/")[0];
                if (fileMimeType.startsWith(`${generalType}/`)) {
                    return true;
                }
            }
        }
    }
    return false;
}
export class CompositeAttachmentAdapter {
    _adapters;
    accept;
    constructor(adapters) {
        this._adapters = adapters;
        const wildcardIdx = adapters.findIndex((a) => a.accept === "*");
        if (wildcardIdx !== -1) {
            if (wildcardIdx !== adapters.length - 1)
                throw new Error("A wildcard adapter (handling all files) can only be specified as the last adapter.");
            this.accept = "*";
        }
        else {
            this.accept = adapters.map((a) => a.accept).join(",");
        }
    }
    add(state) {
        for (const adapter of this._adapters) {
            if (fileMatchesAccept(state.file, adapter.accept)) {
                return adapter.add(state);
            }
        }
        throw new Error("No matching adapter found for file");
    }
    async send(attachment) {
        const adapters = this._adapters.slice();
        for (const adapter of adapters) {
            if (fileMatchesAccept(attachment.file, adapter.accept)) {
                return adapter.send(attachment);
            }
        }
        throw new Error("No matching adapter found for attachment");
    }
    async remove(attachment) {
        const adapters = this._adapters.slice();
        for (const adapter of adapters) {
            if (fileMatchesAccept({
                name: attachment.name,
                type: attachment.contentType,
            }, adapter.accept)) {
                return adapter.remove(attachment);
            }
        }
        throw new Error("No matching adapter found for attachment");
    }
}
//# sourceMappingURL=CompositeAttachmentAdapter.js.map