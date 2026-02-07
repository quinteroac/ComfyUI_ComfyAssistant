"use client";
import { useAuiState } from "./useAuiState.js";
export const AuiIf = ({ children, condition }) => {
    const result = useAuiState(condition);
    return result ? children : null;
};
AuiIf.displayName = "AuiIf";
//# sourceMappingURL=AuiIf.js.map