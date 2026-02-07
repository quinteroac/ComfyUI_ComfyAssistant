declare const contextValue: unique symbol;
type Context<T> = {
    [contextValue]: T;
};
export declare const createResourceContext: <T>(defaultValue: T) => Context<T>;
export declare const withContextProvider: <T, TResult>(context: Context<T>, value: T, fn: () => TResult) => TResult;
export declare const tap: <T>(context: Context<T>) => T;
export {};
//# sourceMappingURL=context.d.ts.map