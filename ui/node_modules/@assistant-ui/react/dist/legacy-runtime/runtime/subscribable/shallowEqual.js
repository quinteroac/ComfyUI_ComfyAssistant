export function shallowEqual(objA, objB) {
    if (objA === undefined && objB === undefined)
        return true;
    if (objA === undefined)
        return false;
    if (objB === undefined)
        return false;
    for (const key of Object.keys(objA)) {
        const valueA = objA[key];
        const valueB = objB[key];
        if (!Object.is(valueA, valueB))
            return false;
    }
    return true;
}
//# sourceMappingURL=shallowEqual.js.map