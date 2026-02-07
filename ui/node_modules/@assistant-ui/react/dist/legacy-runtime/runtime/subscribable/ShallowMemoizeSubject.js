import { shallowEqual } from "./shallowEqual.js";
import { BaseSubject } from "./BaseSubject.js";
import { SKIP_UPDATE } from "./SKIP_UPDATE.js";
export class ShallowMemoizeSubject extends BaseSubject {
    binding;
    get path() {
        return this.binding.path;
    }
    constructor(binding) {
        super();
        this.binding = binding;
        const state = binding.getState();
        if (state === SKIP_UPDATE)
            throw new Error("Entry not available in the store");
        this._previousState = state;
    }
    _previousState;
    getState = () => {
        if (!this.isConnected)
            this._syncState();
        return this._previousState;
    };
    _syncState() {
        const state = this.binding.getState();
        if (state === SKIP_UPDATE)
            return false;
        if (shallowEqual(state, this._previousState))
            return false;
        this._previousState = state;
        return true;
    }
    _connect() {
        const callback = () => {
            if (this._syncState()) {
                this.notifySubscribers();
            }
        };
        return this.binding.subscribe(callback);
    }
}
//# sourceMappingURL=ShallowMemoizeSubject.js.map