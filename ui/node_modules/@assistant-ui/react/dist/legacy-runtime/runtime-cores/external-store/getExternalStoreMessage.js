export const symbolInnerMessage = Symbol("innerMessage");
const symbolInnerMessages = Symbol("innerMessages");
/**
 * @deprecated Use `getExternalStoreMessages` (plural) instead. This function will be removed in 0.12.0.
 */
export const getExternalStoreMessage = (input) => {
    const withInnerMessages = input;
    return withInnerMessages[symbolInnerMessage];
};
const EMPTY_ARRAY = [];
export const getExternalStoreMessages = (input) => {
    // TODO temp until 0.12.0 (migrate useExternalStoreRuntime to always set an array)
    const container = ("messages" in input ? input.messages : input);
    const value = container[symbolInnerMessages] || container[symbolInnerMessage];
    if (!value)
        return EMPTY_ARRAY;
    if (Array.isArray(value)) {
        return value;
    }
    container[symbolInnerMessages] = [value];
    return container[symbolInnerMessages];
};
//# sourceMappingURL=getExternalStoreMessage.js.map