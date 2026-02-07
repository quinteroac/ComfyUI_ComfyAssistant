import React from "react";
const context = React.createContext(!0);
function forbiddenInRender() {
  throw new Error("A function wrapped in useEffectEvent can't be called during rendering.");
}
const isInvalidExecutionContextForEventFunction = "use" in React ? () => {
  try {
    return React.use(context);
  } catch {
    return !1;
  }
} : () => !1;
function useEffectEvent(fn) {
  const ref = React.useRef(forbiddenInRender);
  return React.useInsertionEffect(() => {
    ref.current = fn;
  }, [fn]), (...args) => {
    isInvalidExecutionContextForEventFunction() && forbiddenInRender();
    const latestFn = ref.current;
    return latestFn(...args);
  };
}
export {
  useEffectEvent
};
//# sourceMappingURL=index.js.map
