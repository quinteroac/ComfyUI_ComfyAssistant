export class SimpleTextAttachmentAdapter {
    accept = "text/plain,text/html,text/markdown,text/csv,text/xml,text/json,text/css";
    async add(state) {
        return {
            id: state.file.name,
            type: "document",
            name: state.file.name,
            contentType: state.file.type,
            file: state.file,
            status: { type: "requires-action", reason: "composer-send" },
        };
    }
    async send(attachment) {
        return {
            ...attachment,
            status: { type: "complete" },
            content: [
                {
                    type: "text",
                    text: `<attachment name=${attachment.name}>\n${await getFileText(attachment.file)}\n</attachment>`,
                },
            ],
        };
    }
    async remove() {
        // noop
    }
}
const getFileText = (file) => new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(reader.result);
    reader.onerror = (error) => reject(error);
    reader.readAsText(file);
});
//# sourceMappingURL=SimpleTextAttachmentAdapter.js.map