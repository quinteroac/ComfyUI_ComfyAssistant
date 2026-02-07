export declare namespace tapState {
    type StateUpdater<S> = S | ((prev: S) => S);
}
export declare function tapState<S = undefined>(): [
    S | undefined,
    (updater: tapState.StateUpdater<S>) => void
];
export declare function tapState<S>(initial: S | (() => S)): [S, (updater: tapState.StateUpdater<S>) => void];
//# sourceMappingURL=tap-state.d.ts.map