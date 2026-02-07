import { BaseSubject } from "./BaseSubject.js";
export class NestedSubscriptionSubject extends BaseSubject {
    binding;
    get path() {
        return this.binding.path;
    }
    constructor(binding) {
        super();
        this.binding = binding;
    }
    getState() {
        return this.binding.getState();
    }
    outerSubscribe(callback) {
        return this.binding.subscribe(callback);
    }
    _connect() {
        const callback = () => {
            this.notifySubscribers();
        };
        let lastState = this.binding.getState();
        let innerUnsubscribe = lastState?.subscribe(callback);
        const onRuntimeUpdate = () => {
            const newState = this.binding.getState();
            if (newState === lastState)
                return;
            lastState = newState;
            innerUnsubscribe?.();
            innerUnsubscribe = this.binding.getState()?.subscribe(callback);
            callback();
        };
        const outerUnsubscribe = this.outerSubscribe(onRuntimeUpdate);
        return () => {
            outerUnsubscribe?.();
            innerUnsubscribe?.();
        };
    }
}
//# sourceMappingURL=NestedSubscriptionSubject.js.map