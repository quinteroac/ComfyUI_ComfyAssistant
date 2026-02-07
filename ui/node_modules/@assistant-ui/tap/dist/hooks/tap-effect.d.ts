export declare namespace tapEffect {
    type Destructor = () => void;
    type EffectCallback = () => void | Destructor;
}
export declare function tapEffect(effect: tapEffect.EffectCallback): void;
export declare function tapEffect(effect: tapEffect.EffectCallback, deps: readonly unknown[]): void;
//# sourceMappingURL=tap-effect.d.ts.map