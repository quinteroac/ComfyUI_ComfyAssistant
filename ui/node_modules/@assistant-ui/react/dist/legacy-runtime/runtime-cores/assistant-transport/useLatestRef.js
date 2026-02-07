import { useEffect, useRef } from "react";
export function useLatestRef(value) {
    const ref = useRef(value);
    useEffect(() => {
        ref.current = value;
    }, [value]);
    return ref;
}
//# sourceMappingURL=useLatestRef.js.map