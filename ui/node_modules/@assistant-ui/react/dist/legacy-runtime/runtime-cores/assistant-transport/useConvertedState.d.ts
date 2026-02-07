import type { AssistantTransportCommand, AssistantTransportState, AssistantTransportStateConverter } from "./types.js";
import type { ToolExecutionStatus } from "./useToolInvocations.js";
export declare function useConvertedState<T>(converter: AssistantTransportStateConverter<T>, agentState: T, pendingCommands: AssistantTransportCommand[], isSending: boolean, toolStatuses: Record<string, ToolExecutionStatus>): AssistantTransportState;
//# sourceMappingURL=useConvertedState.d.ts.map