import { BaseAssistantRuntimeCore } from "../core/BaseAssistantRuntimeCore.js";
import { ExternalStoreThreadListRuntimeCore } from "./ExternalStoreThreadListRuntimeCore.js";
import { ExternalStoreAdapter } from "./ExternalStoreAdapter.js";
export declare class ExternalStoreRuntimeCore extends BaseAssistantRuntimeCore {
    readonly threads: ExternalStoreThreadListRuntimeCore;
    constructor(adapter: ExternalStoreAdapter<any>);
    setAdapter(adapter: ExternalStoreAdapter<any>): void;
}
//# sourceMappingURL=ExternalStoreRuntimeCore.d.ts.map