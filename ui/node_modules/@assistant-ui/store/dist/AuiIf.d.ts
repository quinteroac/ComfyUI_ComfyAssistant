import type { FC, PropsWithChildren } from "react";
import type { AssistantState } from "./types/client.js";
export declare namespace AuiIf {
    type Props = PropsWithChildren<{
        condition: AuiIf.Condition;
    }>;
    type Condition = (state: AssistantState) => boolean;
}
export declare const AuiIf: FC<AuiIf.Props>;
//# sourceMappingURL=AuiIf.d.ts.map