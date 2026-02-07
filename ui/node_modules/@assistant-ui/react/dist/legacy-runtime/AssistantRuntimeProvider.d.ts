import { FC, PropsWithChildren } from "react";
import { AssistantClient } from "@assistant-ui/store";
import { AssistantRuntime } from "./runtime/AssistantRuntime.js";
export declare namespace AssistantRuntimeProvider {
    type Props = PropsWithChildren<{
        /**
         * The runtime to provide to the rest of your app.
         */
        runtime: AssistantRuntime;
        /**
         * The aui instance to extend. If not provided, a new aui instance will be created.
         */
        aui?: AssistantClient;
    }>;
}
export declare const AssistantRuntimeProviderImpl: FC<AssistantRuntimeProvider.Props>;
export declare const AssistantRuntimeProvider: import("react").NamedExoticComponent<AssistantRuntimeProvider.Props>;
//# sourceMappingURL=AssistantRuntimeProvider.d.ts.map