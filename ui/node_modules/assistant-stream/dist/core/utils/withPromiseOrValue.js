export function withPromiseOrValue(callback, thenHandler, catchHandler) {
    try {
        const promiseOrValue = callback();
        if (typeof promiseOrValue === "object" &&
            promiseOrValue !== null &&
            "then" in promiseOrValue) {
            return promiseOrValue.then(thenHandler, catchHandler);
        }
        else {
            thenHandler(promiseOrValue);
        }
    }
    catch (e) {
        catchHandler(e);
    }
}
//# sourceMappingURL=withPromiseOrValue.js.map