async function* streamGeneratorPolyfill() {
    const reader = this.getReader();
    try {
        while (true) {
            const { done, value } = await reader.read();
            if (done)
                break;
            yield value;
        }
    }
    finally {
        reader.releaseLock();
    }
}
export function asAsyncIterableStream(source) {
    source[Symbol.asyncIterator] ??=
        streamGeneratorPolyfill;
    return source;
}
//# sourceMappingURL=AsyncIterableStream.js.map