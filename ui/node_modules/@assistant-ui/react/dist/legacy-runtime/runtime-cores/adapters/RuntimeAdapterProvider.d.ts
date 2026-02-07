import { FC, ReactNode } from "react";
import { ThreadHistoryAdapter } from "./thread-history/ThreadHistoryAdapter.js";
import { AttachmentAdapter } from "./attachment/AttachmentAdapter.js";
import { ModelContextProvider } from "../../../model-context/index.js";
export type RuntimeAdapters = {
    modelContext?: ModelContextProvider;
    history?: ThreadHistoryAdapter;
    attachments?: AttachmentAdapter;
};
export declare namespace RuntimeAdapterProvider {
    type Props = {
        adapters: RuntimeAdapters;
        children: ReactNode;
    };
}
export declare const RuntimeAdapterProvider: FC<RuntimeAdapterProvider.Props>;
export declare const useRuntimeAdapters: () => RuntimeAdapters | null;
//# sourceMappingURL=RuntimeAdapterProvider.d.ts.map