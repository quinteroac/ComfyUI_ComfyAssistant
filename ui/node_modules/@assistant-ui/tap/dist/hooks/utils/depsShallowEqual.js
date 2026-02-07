export const depsShallowEqual = (a, b) => {
    if (a.length !== b.length)
        return false;
    for (let i = 0; i < a.length; i++) {
        if (!Object.is(a[i], b[i]))
            return false;
    }
    return true;
};
//# sourceMappingURL=depsShallowEqual.js.map