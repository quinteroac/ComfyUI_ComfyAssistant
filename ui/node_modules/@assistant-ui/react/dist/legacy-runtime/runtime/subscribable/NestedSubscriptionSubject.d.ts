import { Unsubscribe } from "../../../types/index.js";
import { BaseSubject } from "./BaseSubject.js";
import { NestedSubscribable, Subscribable, SubscribableWithState } from "./Subscribable.js";
export declare class NestedSubscriptionSubject<TState extends Subscribable | undefined, TPath> extends BaseSubject implements SubscribableWithState<TState, TPath>, NestedSubscribable<TState, TPath> {
    private binding;
    get path(): TPath;
    constructor(binding: NestedSubscribable<TState, TPath>);
    getState(): TState;
    outerSubscribe(callback: () => void): Unsubscribe;
    protected _connect(): Unsubscribe;
}
//# sourceMappingURL=NestedSubscriptionSubject.d.ts.map