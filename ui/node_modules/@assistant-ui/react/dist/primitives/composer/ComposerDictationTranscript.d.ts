import { Primitive } from "@radix-ui/react-primitive";
import { type ComponentRef, ComponentPropsWithoutRef } from "react";
export declare namespace ComposerPrimitiveDictationTranscript {
    type Element = ComponentRef<typeof Primitive.span>;
    type Props = ComponentPropsWithoutRef<typeof Primitive.span>;
}
/**
 * Renders the current interim (partial) transcript while dictation is active.
 *
 * This component displays real-time feedback of what the user is saying before
 * the transcription is finalized and committed to the composer input.
 *
 * @example
 * ```tsx
 * <ComposerPrimitive.If dictation>
 *   <div className="dictation-preview">
 *     <ComposerPrimitive.DictationTranscript />
 *   </div>
 * </ComposerPrimitive.If>
 * ```
 */
export declare const ComposerPrimitiveDictationTranscript: import("react").ForwardRefExoticComponent<Omit<import("react").ClassAttributes<HTMLSpanElement> & import("react").HTMLAttributes<HTMLSpanElement> & {
    asChild?: boolean;
}, "ref"> & import("react").RefAttributes<HTMLSpanElement>>;
//# sourceMappingURL=ComposerDictationTranscript.d.ts.map