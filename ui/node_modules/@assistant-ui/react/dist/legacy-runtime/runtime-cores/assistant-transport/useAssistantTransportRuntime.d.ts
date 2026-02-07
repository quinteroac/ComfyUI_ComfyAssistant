import { AssistantRuntime } from "../../runtime/AssistantRuntime.js";
import { AssistantTransportOptions, AssistantTransportCommand } from "./types.js";
import { UserExternalState } from "../../../augmentations.js";
export declare const useAssistantTransportSendCommand: () => (command: AssistantTransportCommand) => void;
export declare function useAssistantTransportState(): UserExternalState;
export declare function useAssistantTransportState<T>(selector: (state: UserExternalState) => T): T;
/**
 * @alpha This is an experimental API that is subject to change.
 */
export declare const useAssistantTransportRuntime: <T>(options: AssistantTransportOptions<T>) => AssistantRuntime;
//# sourceMappingURL=useAssistantTransportRuntime.d.ts.map