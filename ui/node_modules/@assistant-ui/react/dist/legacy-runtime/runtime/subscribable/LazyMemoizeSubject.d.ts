import { BaseSubject } from "./BaseSubject.js";
import { SKIP_UPDATE } from "./SKIP_UPDATE.js";
import { SubscribableWithState } from "./Subscribable.js";
export declare class LazyMemoizeSubject<TState extends object, TPath> extends BaseSubject implements SubscribableWithState<TState, TPath> {
    private binding;
    get path(): TPath;
    constructor(binding: SubscribableWithState<TState | SKIP_UPDATE, TPath>);
    private _previousStateDirty;
    private _previousState;
    getState: () => TState;
    protected _connect(): import("../../..").Unsubscribe;
}
//# sourceMappingURL=LazyMemoizeSubject.d.ts.map