export declare namespace tapRef {
    interface RefObject<T> {
        current: T;
    }
}
export declare function tapRef<T>(initialValue: T): tapRef.RefObject<T>;
export declare function tapRef<T = undefined>(): tapRef.RefObject<T | undefined>;
//# sourceMappingURL=tap-ref.d.ts.map