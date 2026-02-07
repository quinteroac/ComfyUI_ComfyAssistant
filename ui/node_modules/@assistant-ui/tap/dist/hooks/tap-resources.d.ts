import { ExtractResourceReturnType, ResourceElement } from "../core/types.js";
export declare function tapResources<E extends ResourceElement<any, any>>(getElements: () => readonly E[], getElementsDeps?: readonly unknown[]): ExtractResourceReturnType<E>[];
//# sourceMappingURL=tap-resources.d.ts.map