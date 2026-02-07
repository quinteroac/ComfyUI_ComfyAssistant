import { BaseSubject } from "./BaseSubject.js";
import { SKIP_UPDATE } from "./SKIP_UPDATE.js";
export class LazyMemoizeSubject extends BaseSubject {
    binding;
    get path() {
        return this.binding.path;
    }
    constructor(binding) {
        super();
        this.binding = binding;
    }
    _previousStateDirty = true;
    _previousState;
    getState = () => {
        if (!this.isConnected || this._previousStateDirty) {
            const newState = this.binding.getState();
            if (newState !== SKIP_UPDATE) {
                this._previousState = newState;
            }
            this._previousStateDirty = false;
        }
        if (this._previousState === undefined)
            throw new Error("Entry not available in the store");
        return this._previousState;
    };
    _connect() {
        const callback = () => {
            this._previousStateDirty = true;
            this.notifySubscribers();
        };
        return this.binding.subscribe(callback);
    }
}
//# sourceMappingURL=LazyMemoizeSubject.js.map