"use client";
import { jsx as _jsx } from "react/jsx-runtime";
import { INTERNAL, useMessagePartText } from "@assistant-ui/react";
import { forwardRef, useMemo, } from "react";
import ReactMarkdown from "react-markdown";
import { PreOverride } from "../overrides/PreOverride.js";
import { DefaultPre, DefaultCode, DefaultCodeBlockContent, DefaultCodeHeader, } from "../overrides/defaultComponents.js";
import { useCallbackRef } from "@radix-ui/react-use-callback-ref";
import { CodeOverride } from "../overrides/CodeOverride.js";
import classNames from "classnames";
const { useSmooth, useSmoothStatus, withSmoothContextProvider } = INTERNAL;
const MarkdownTextInner = ({ components: userComponents, componentsByLanguage, smooth = true, preprocess, ...rest }) => {
    const messagePartText = useMessagePartText();
    const processedMessagePart = useMemo(() => {
        if (!preprocess)
            return messagePartText;
        return {
            ...messagePartText,
            text: preprocess(messagePartText.text),
        };
    }, [messagePartText, preprocess]);
    const { text } = useSmooth(processedMessagePart, smooth);
    const { pre = DefaultPre, code = DefaultCode, SyntaxHighlighter = DefaultCodeBlockContent, CodeHeader = DefaultCodeHeader, } = userComponents ?? {};
    const useCodeOverrideComponents = useMemo(() => {
        return {
            Pre: pre,
            Code: code,
            SyntaxHighlighter,
            CodeHeader,
        };
    }, [pre, code, SyntaxHighlighter, CodeHeader]);
    const CodeComponent = useCallbackRef((props) => (_jsx(CodeOverride, { components: useCodeOverrideComponents, componentsByLanguage: componentsByLanguage, ...props })));
    const components = useMemo(() => {
        const { pre, code, SyntaxHighlighter, CodeHeader, ...componentsRest } = userComponents ?? {};
        return {
            ...componentsRest,
            pre: PreOverride,
            code: CodeComponent,
        };
    }, [CodeComponent, userComponents]);
    return (_jsx(ReactMarkdown, { components: components, ...rest, children: text }));
};
const MarkdownTextPrimitiveImpl = forwardRef(({ className, containerProps, containerComponent: Container = "div", ...rest }, forwardedRef) => {
    const status = useSmoothStatus();
    return (_jsx(Container, { "data-status": status.type, ...containerProps, className: classNames(className, containerProps?.className), ref: forwardedRef, children: _jsx(MarkdownTextInner, { ...rest }) }));
});
MarkdownTextPrimitiveImpl.displayName = "MarkdownTextPrimitive";
export const MarkdownTextPrimitive = withSmoothContextProvider(MarkdownTextPrimitiveImpl);
//# sourceMappingURL=MarkdownText.js.map