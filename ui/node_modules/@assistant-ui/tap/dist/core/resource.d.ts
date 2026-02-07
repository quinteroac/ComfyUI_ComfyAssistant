import { ResourceElement } from "./types.js";
export declare function resource<R>(fn: () => R): () => ResourceElement<R, undefined>;
export declare function resource<R, P>(fn: (props: P) => R): (props: P) => ResourceElement<R, P>;
export declare function resource<R, P>(fn: (props?: P) => R): (props?: P) => ResourceElement<R, P | undefined>;
//# sourceMappingURL=resource.d.ts.map