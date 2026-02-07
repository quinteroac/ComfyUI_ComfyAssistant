"use client";
import { useRemoteThreadListRuntime } from "../runtime-cores/remote-thread-list/useRemoteThreadListRuntime.js";
import { useCloudThreadListAdapter } from "../runtime-cores/remote-thread-list/adapter/cloud.js";
export const useCloudThreadListRuntime = ({ runtimeHook, ...adapterOptions }) => {
    const adapter = useCloudThreadListAdapter(adapterOptions);
    const runtime = useRemoteThreadListRuntime({
        runtimeHook: runtimeHook,
        adapter,
        allowNesting: true,
    });
    return runtime;
};
//# sourceMappingURL=useCloudThreadListRuntime.js.map