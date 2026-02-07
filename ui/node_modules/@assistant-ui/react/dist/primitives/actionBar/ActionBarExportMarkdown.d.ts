import { ActionButtonProps } from "../../utils/createActionButton.js";
declare const useActionBarExportMarkdown: ({ filename, onExport, }?: {
    filename?: string | undefined;
    onExport?: ((content: string) => void | Promise<void>) | undefined;
}) => (() => Promise<void>) | null;
export declare namespace ActionBarPrimitiveExportMarkdown {
    type Element = HTMLButtonElement;
    type Props = ActionButtonProps<typeof useActionBarExportMarkdown>;
}
export declare const ActionBarPrimitiveExportMarkdown: import("react").ForwardRefExoticComponent<Omit<import("react").ClassAttributes<HTMLButtonElement> & import("react").ButtonHTMLAttributes<HTMLButtonElement> & {
    asChild?: boolean;
}, "ref"> & {
    filename?: string | undefined;
    onExport?: ((content: string) => void | Promise<void>) | undefined;
} & import("react").RefAttributes<HTMLButtonElement>>;
export {};
//# sourceMappingURL=ActionBarExportMarkdown.d.ts.map