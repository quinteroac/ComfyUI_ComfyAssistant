import type { ActionButtonElement, ActionButtonProps } from "../../utils/createActionButton.js";
declare const useComposerStopDictation: () => (() => void) | null;
export declare namespace ComposerPrimitiveStopDictation {
    type Element = ActionButtonElement;
    type Props = ActionButtonProps<typeof useComposerStopDictation>;
}
/**
 * A button that stops the current dictation session.
 *
 * Only rendered when dictation is active.
 *
 * @example
 * ```tsx
 * <ComposerPrimitive.StopDictation>
 *   <StopIcon />
 * </ComposerPrimitive.StopDictation>
 * ```
 */
export declare const ComposerPrimitiveStopDictation: import("react").ForwardRefExoticComponent<Omit<import("react").ClassAttributes<HTMLButtonElement> & import("react").ButtonHTMLAttributes<HTMLButtonElement> & {
    asChild?: boolean;
}, "ref"> & import("react").RefAttributes<HTMLButtonElement>>;
export {};
//# sourceMappingURL=ComposerStopDictation.d.ts.map