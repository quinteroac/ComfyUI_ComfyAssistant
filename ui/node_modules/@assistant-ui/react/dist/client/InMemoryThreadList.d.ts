import { type ClientOutput } from "@assistant-ui/store";
import type { ResourceElement } from "@assistant-ui/tap";
export type InMemoryThreadListProps = {
    thread: (threadId: string) => ResourceElement<ClientOutput<"thread">>;
    onSwitchToThread?: (threadId: string) => void;
    onSwitchToNewThread?: () => void;
};
export declare const InMemoryThreadList: (props: InMemoryThreadListProps) => ResourceElement<ClientOutput<"threads">, InMemoryThreadListProps>;
//# sourceMappingURL=InMemoryThreadList.d.ts.map