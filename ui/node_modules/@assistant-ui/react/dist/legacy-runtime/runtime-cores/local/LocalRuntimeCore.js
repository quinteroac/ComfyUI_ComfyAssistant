import { BaseAssistantRuntimeCore } from "../core/BaseAssistantRuntimeCore.js";
import { LocalThreadRuntimeCore } from "./LocalThreadRuntimeCore.js";
import { LocalThreadListRuntimeCore } from "./LocalThreadListRuntimeCore.js";
import { ExportedMessageRepository } from "../utils/MessageRepository.js";
export class LocalRuntimeCore extends BaseAssistantRuntimeCore {
    threads;
    Provider = undefined;
    _options;
    constructor(options, initialMessages) {
        super();
        this._options = options;
        this.threads = new LocalThreadListRuntimeCore(() => {
            return new LocalThreadRuntimeCore(this._contextProvider, this._options);
        });
        if (initialMessages) {
            this.threads
                .getMainThreadRuntimeCore()
                .import(ExportedMessageRepository.fromArray(initialMessages));
        }
    }
}
//# sourceMappingURL=LocalRuntimeCore.js.map