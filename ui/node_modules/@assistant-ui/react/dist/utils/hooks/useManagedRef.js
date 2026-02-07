import { useCallback, useRef } from "react";
export const useManagedRef = (callback) => {
    const cleanupRef = useRef(undefined);
    const ref = useCallback((el) => {
        // Call the previous cleanup function
        if (cleanupRef.current) {
            cleanupRef.current();
        }
        // Call the new callback and store its cleanup function
        if (el) {
            cleanupRef.current = callback(el);
        }
    }, [callback]);
    return ref;
};
//# sourceMappingURL=useManagedRef.js.map