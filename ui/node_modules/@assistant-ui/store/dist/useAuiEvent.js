import { useEffect } from "react";
import { useEffectEvent } from "use-effect-event";
import { useAui } from "./useAui.js";
import { normalizeEventSelector } from "./types/events.js";
export const useAuiEvent = (selector, callback) => {
    const aui = useAui();
    const callbackRef = useEffectEvent(callback);
    const { scope, event } = normalizeEventSelector(selector);
    useEffect(() => aui.on({ scope, event }, callbackRef), [aui, scope, event, callbackRef]);
};
//# sourceMappingURL=useAuiEvent.js.map