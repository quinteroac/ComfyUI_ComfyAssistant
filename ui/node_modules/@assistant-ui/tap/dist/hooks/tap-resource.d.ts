import { ExtractResourceReturnType, ResourceElement } from "../core/types.js";
export declare function tapResource<E extends ResourceElement<any, any>>(element: E): ExtractResourceReturnType<E>;
export declare function tapResource<E extends ResourceElement<any, any>>(element: E, propsDeps: readonly unknown[]): ExtractResourceReturnType<E>;
//# sourceMappingURL=tap-resource.d.ts.map