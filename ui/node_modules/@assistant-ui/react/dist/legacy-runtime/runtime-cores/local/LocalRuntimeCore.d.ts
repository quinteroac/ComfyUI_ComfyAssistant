import { BaseAssistantRuntimeCore } from "../core/BaseAssistantRuntimeCore.js";
import { LocalRuntimeOptionsBase } from "./LocalRuntimeOptions.js";
import { LocalThreadListRuntimeCore } from "./LocalThreadListRuntimeCore.js";
import { ThreadMessageLike } from "../external-store/index.js";
export declare class LocalRuntimeCore extends BaseAssistantRuntimeCore {
    readonly threads: LocalThreadListRuntimeCore;
    readonly Provider: undefined;
    private _options;
    constructor(options: LocalRuntimeOptionsBase, initialMessages: readonly ThreadMessageLike[] | undefined);
}
//# sourceMappingURL=LocalRuntimeCore.d.ts.map