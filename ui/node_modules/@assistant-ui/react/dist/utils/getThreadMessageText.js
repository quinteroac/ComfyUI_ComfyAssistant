export const getThreadMessageText = (message) => {
    const textParts = message.content.filter((part) => part.type === "text");
    return textParts.map((part) => part.text).join("\n\n");
};
//# sourceMappingURL=getThreadMessageText.js.map