import { ComponentType, FC, PropsWithChildren } from "react";
import { ReadonlyStore } from "../../context/ReadonlyStore.js";
export declare const SmoothContextProvider: FC<PropsWithChildren>;
export declare const withSmoothContextProvider: <C extends ComponentType<any>>(Component: C) => C;
export declare const useSmoothStatus: {
    (): {
        readonly type: "running";
    } | {
        readonly type: "complete";
    } | {
        readonly type: "incomplete";
        readonly reason: "cancelled" | "length" | "content-filter" | "other" | "error";
        readonly error?: unknown;
    } | {
        readonly type: "requires-action";
        readonly reason: "interrupt";
    };
    <TSelected>(selector: (state: {
        readonly type: "running";
    } | {
        readonly type: "complete";
    } | {
        readonly type: "incomplete";
        readonly reason: "cancelled" | "length" | "content-filter" | "other" | "error";
        readonly error?: unknown;
    } | {
        readonly type: "requires-action";
        readonly reason: "interrupt";
    }) => TSelected): TSelected;
    (options: {
        optional: true;
    }): {
        readonly type: "running";
    } | {
        readonly type: "complete";
    } | {
        readonly type: "incomplete";
        readonly reason: "cancelled" | "length" | "content-filter" | "other" | "error";
        readonly error?: unknown;
    } | {
        readonly type: "requires-action";
        readonly reason: "interrupt";
    } | null;
    <TSelected>(options: {
        optional: true;
        selector?: (state: {
            readonly type: "running";
        } | {
            readonly type: "complete";
        } | {
            readonly type: "incomplete";
            readonly reason: "cancelled" | "length" | "content-filter" | "other" | "error";
            readonly error?: unknown;
        } | {
            readonly type: "requires-action";
            readonly reason: "interrupt";
        }) => TSelected;
    }): TSelected | null;
}, useSmoothStatusStore: {
    (): ReadonlyStore<{
        readonly type: "running";
    } | {
        readonly type: "complete";
    } | {
        readonly type: "incomplete";
        readonly reason: "cancelled" | "length" | "content-filter" | "other" | "error";
        readonly error?: unknown;
    } | {
        readonly type: "requires-action";
        readonly reason: "interrupt";
    }>;
    (options: {
        optional: true;
    }): ReadonlyStore<{
        readonly type: "running";
    } | {
        readonly type: "complete";
    } | {
        readonly type: "incomplete";
        readonly reason: "cancelled" | "length" | "content-filter" | "other" | "error";
        readonly error?: unknown;
    } | {
        readonly type: "requires-action";
        readonly reason: "interrupt";
    }> | null;
};
//# sourceMappingURL=SmoothContext.d.ts.map