import { Unsubscribe } from "../../../types/index.js";
export declare class BaseSubscribable {
    private _subscribers;
    subscribe(callback: () => void): Unsubscribe;
    waitForUpdate(): Promise<void>;
    protected _notifySubscribers(): void;
}
//# sourceMappingURL=BaseSubscribable.d.ts.map