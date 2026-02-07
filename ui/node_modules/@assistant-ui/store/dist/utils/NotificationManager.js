import { resource } from "@assistant-ui/tap";
import { tapConst } from "@assistant-ui/tap";
export const NotificationManager = resource(() => {
    return tapConst(() => {
        const listeners = new Map();
        const wildcardListeners = new Set();
        const subscribers = new Set();
        return {
            on(event, callback) {
                const cb = callback;
                if (event === "*") {
                    wildcardListeners.add(cb);
                    return () => wildcardListeners.delete(cb);
                }
                let set = listeners.get(event);
                if (!set) {
                    set = new Set();
                    listeners.set(event, set);
                }
                set.add(cb);
                return () => {
                    set.delete(cb);
                    if (set.size === 0)
                        listeners.delete(event);
                };
            },
            emit(event, payload, clientStack) {
                const eventListeners = listeners.get(event);
                if (!eventListeners && wildcardListeners.size === 0)
                    return;
                queueMicrotask(() => {
                    const errors = [];
                    if (eventListeners) {
                        for (const cb of eventListeners) {
                            try {
                                cb(payload, clientStack);
                            }
                            catch (e) {
                                errors.push(e);
                            }
                        }
                    }
                    if (wildcardListeners.size > 0) {
                        const wrapped = { event, payload };
                        for (const cb of wildcardListeners) {
                            try {
                                cb(wrapped, clientStack);
                            }
                            catch (e) {
                                errors.push(e);
                            }
                        }
                    }
                    if (errors.length > 0) {
                        if (errors.length === 1) {
                            throw errors[0];
                        }
                        else {
                            for (const error of errors) {
                                console.error(error);
                            }
                            throw new AggregateError(errors, "Errors occurred during event emission");
                        }
                    }
                });
            },
            subscribe(callback) {
                subscribers.add(callback);
                return () => subscribers.delete(callback);
            },
            notifySubscribers() {
                for (const cb of subscribers) {
                    try {
                        cb();
                    }
                    catch (e) {
                        console.error("NotificationManager: subscriber callback error", e);
                    }
                }
            },
        };
    }, []);
});
//# sourceMappingURL=NotificationManager.js.map