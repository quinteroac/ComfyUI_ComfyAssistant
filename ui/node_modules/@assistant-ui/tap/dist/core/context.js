const contextValue = Symbol("tap.Context");
export const createResourceContext = (defaultValue) => {
    return {
        [contextValue]: defaultValue,
    };
};
export const withContextProvider = (context, value, fn) => {
    const previousValue = context[contextValue];
    context[contextValue] = value;
    try {
        return fn();
    }
    finally {
        context[contextValue] = previousValue;
    }
};
export const tap = (context) => {
    return context[contextValue];
};
//# sourceMappingURL=context.js.map