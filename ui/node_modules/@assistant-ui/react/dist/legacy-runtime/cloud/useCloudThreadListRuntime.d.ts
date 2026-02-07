import { AssistantCloud } from "assistant-cloud";
import { AssistantRuntime } from "../runtime/index.js";
type ThreadData = {
    externalId: string;
};
type CloudThreadListAdapter = {
    cloud: AssistantCloud;
    runtimeHook: () => AssistantRuntime;
    create?(): Promise<ThreadData>;
    delete?(threadId: string): Promise<void>;
};
export declare const useCloudThreadListRuntime: ({ runtimeHook, ...adapterOptions }: CloudThreadListAdapter) => AssistantRuntime;
export {};
//# sourceMappingURL=useCloudThreadListRuntime.d.ts.map