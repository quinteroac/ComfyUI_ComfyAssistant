"use strict";
Object.defineProperty(exports, "__esModule", { value: !0 });
var React = require("react");
function _interopDefaultCompat(e) {
  return e && typeof e == "object" && "default" in e ? e : { default: e };
}
var React__default = /* @__PURE__ */ _interopDefaultCompat(React);
const context = React__default.default.createContext(!0);
function forbiddenInRender() {
  throw new Error("A function wrapped in useEffectEvent can't be called during rendering.");
}
const isInvalidExecutionContextForEventFunction = "use" in React__default.default ? () => {
  try {
    return React__default.default.use(context);
  } catch {
    return !1;
  }
} : () => !1;
function useEffectEvent(fn) {
  const ref = React__default.default.useRef(forbiddenInRender);
  return React__default.default.useInsertionEffect(() => {
    ref.current = fn;
  }, [fn]), (...args) => {
    isInvalidExecutionContextForEventFunction() && forbiddenInRender();
    const latestFn = ref.current;
    return latestFn(...args);
  };
}
exports.useEffectEvent = useEffectEvent;
//# sourceMappingURL=index.cjs.map
