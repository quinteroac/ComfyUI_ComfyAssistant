const debugVerifyPrototype = (runtime, prototype) => {
    const unboundMethods = Object.getOwnPropertyNames(prototype).filter((methodStr) => {
        const descriptor = Object.getOwnPropertyDescriptor(prototype, methodStr);
        const isMethod = descriptor && typeof descriptor.value === "function";
        if (!isMethod)
            return false;
        const methodName = methodStr;
        return (isMethod &&
            !methodName.startsWith("_") &&
            methodName !== "constructor" &&
            prototype[methodName] === runtime[methodName]);
    });
    if (unboundMethods.length > 0) {
        throw new Error(`The following methods are not bound: ${JSON.stringify(unboundMethods)}`);
    }
    const prototypePrototype = Object.getPrototypeOf(prototype);
    if (prototypePrototype && prototypePrototype !== Object.prototype) {
        debugVerifyPrototype(runtime, prototypePrototype);
    }
};
export const ensureBinding = (r) => {
    const runtime = r;
    if (runtime.__isBound)
        return;
    runtime.__internal_bindMethods?.();
    runtime.__isBound = true;
    if (process.env["NODE_ENV"] !== "production") {
        debugVerifyPrototype(runtime, Object.getPrototypeOf(runtime));
    }
};
//# sourceMappingURL=ensureBinding.js.map