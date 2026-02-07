import sjson from "secure-json-parse";
import { fixJson } from "./fix-json.js";
const PARTIAL_JSON_OBJECT_META_SYMBOL = Symbol("aui.parse-partial-json-object.meta");
export const getPartialJsonObjectMeta = (obj) => {
    return obj?.[PARTIAL_JSON_OBJECT_META_SYMBOL];
};
export const parsePartialJsonObject = (json) => {
    if (json.length === 0)
        return {
            [PARTIAL_JSON_OBJECT_META_SYMBOL]: { state: "partial", partialPath: [] },
        };
    try {
        const res = sjson.parse(json);
        if (typeof res !== "object" || res === null)
            throw new Error("argsText is expected to be an object");
        res[PARTIAL_JSON_OBJECT_META_SYMBOL] = {
            state: "complete",
            partialPath: [],
        };
        return res;
    }
    catch {
        try {
            const [fixedJson, partialPath] = fixJson(json);
            const res = sjson.parse(fixedJson);
            if (typeof res !== "object" || res === null)
                throw new Error("argsText is expected to be an object");
            res[PARTIAL_JSON_OBJECT_META_SYMBOL] = {
                state: "partial",
                partialPath,
            };
            return res;
        }
        catch {
            return undefined;
        }
    }
};
const getFieldState = (parent, parentMeta, fieldPath) => {
    if (typeof parent !== "object" || parent === null)
        return parentMeta.state;
    // 1) parent is complete: return "complete"
    if (parentMeta.state === "complete")
        return "complete";
    // 2) we finished traversing: return parent state
    if (fieldPath.length === 0)
        return parentMeta.state;
    const [field, ...restPath] = fieldPath;
    // 3) field doesn't yet exist in parent: return "partial"
    if (!Object.prototype.hasOwnProperty.call(parent, field))
        return "partial";
    const [partialField, ...restPartialPath] = parentMeta.partialPath;
    // 4) field exists but is not partial: return "complete"
    if (field !== partialField)
        return "complete";
    // 5) field exists and is partial: return child state
    const child = parent[field];
    const childMeta = {
        state: "partial",
        partialPath: restPartialPath,
    };
    return getFieldState(child, childMeta, restPath);
};
export const getPartialJsonObjectFieldState = (obj, fieldPath) => {
    const meta = getPartialJsonObjectMeta(obj);
    if (!meta)
        throw new Error("unable to determine object state");
    return getFieldState(obj, meta, fieldPath.map(String));
};
//# sourceMappingURL=parse-partial-json-object.js.map