import { useMemo } from "react";
export function useConvertedState(converter, agentState, pendingCommands, isSending, toolStatuses) {
    return useMemo(() => converter(agentState, { pendingCommands, isSending, toolStatuses }), [converter, agentState, pendingCommands, isSending, toolStatuses]);
}
//# sourceMappingURL=useConvertedState.js.map