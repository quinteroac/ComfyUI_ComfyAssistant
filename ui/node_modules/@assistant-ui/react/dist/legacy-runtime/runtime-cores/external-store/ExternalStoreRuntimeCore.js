import { BaseAssistantRuntimeCore } from "../core/BaseAssistantRuntimeCore.js";
import { ExternalStoreThreadListRuntimeCore } from "./ExternalStoreThreadListRuntimeCore.js";
import { ExternalStoreThreadRuntimeCore } from "./ExternalStoreThreadRuntimeCore.js";
const getThreadListAdapter = (store) => {
    return store.adapters?.threadList ?? {};
};
export class ExternalStoreRuntimeCore extends BaseAssistantRuntimeCore {
    threads;
    constructor(adapter) {
        super();
        this.threads = new ExternalStoreThreadListRuntimeCore(getThreadListAdapter(adapter), () => new ExternalStoreThreadRuntimeCore(this._contextProvider, adapter));
    }
    setAdapter(adapter) {
        // Update the thread list adapter and propagate store changes to the main thread
        this.threads.__internal_setAdapter(getThreadListAdapter(adapter));
        this.threads.getMainThreadRuntimeCore().__internal_setAdapter(adapter);
    }
}
//# sourceMappingURL=ExternalStoreRuntimeCore.js.map