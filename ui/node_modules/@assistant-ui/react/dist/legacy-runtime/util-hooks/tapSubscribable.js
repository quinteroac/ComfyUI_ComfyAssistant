import { tapState, tapEffect } from "@assistant-ui/tap";
export const tapSubscribable = (subscribable) => {
    const [, setState] = tapState(subscribable.getState);
    tapEffect(() => {
        setState(subscribable.getState());
        return subscribable.subscribe(() => {
            setState(subscribable.getState());
        });
    }, [subscribable]);
    return subscribable.getState();
};
//# sourceMappingURL=tapSubscribable.js.map