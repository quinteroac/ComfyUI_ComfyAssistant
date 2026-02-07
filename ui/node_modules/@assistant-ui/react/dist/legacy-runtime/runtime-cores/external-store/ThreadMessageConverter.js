export class ThreadMessageConverter {
    cache = new WeakMap();
    convertMessages(messages, converter) {
        return messages.map((m, idx) => {
            const cached = this.cache.get(m);
            const newMessage = converter(cached, m, idx);
            this.cache.set(m, newMessage);
            return newMessage;
        });
    }
}
//# sourceMappingURL=ThreadMessageConverter.js.map