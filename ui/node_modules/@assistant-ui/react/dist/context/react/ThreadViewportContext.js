"use client";
import { createContext } from "react";
import { createContextHook } from "./utils/createContextHook.js";
import { createContextStoreHook } from "./utils/createContextStoreHook.js";
export const ThreadViewportContext = createContext(null);
const useThreadViewportContext = createContextHook(ThreadViewportContext, "ThreadPrimitive.Viewport");
export const { useThreadViewport, useThreadViewportStore } = createContextStoreHook(useThreadViewportContext, "useThreadViewport");
//# sourceMappingURL=ThreadViewportContext.js.map