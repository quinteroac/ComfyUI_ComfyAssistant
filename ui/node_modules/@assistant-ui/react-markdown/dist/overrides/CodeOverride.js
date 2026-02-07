import { jsx as _jsx } from "react/jsx-runtime";
import { memo, useContext, } from "react";
import { PreContext, useIsMarkdownCodeBlock } from "./PreOverride.js";
import { DefaultCodeBlock } from "./CodeBlock.js";
import { useCallbackRef } from "@radix-ui/react-use-callback-ref";
import { withDefaultProps } from "./withDefaults.js";
import { DefaultCodeBlockContent } from "./defaultComponents.js";
import { memoCompareNodes } from "../memoization.js";
const CodeBlockOverride = ({ node, components: { Pre, Code, SyntaxHighlighter: FallbackSyntaxHighlighter, CodeHeader: FallbackCodeHeader, }, componentsByLanguage = {}, children, ...codeProps }) => {
    const preProps = useContext(PreContext);
    const getPreProps = withDefaultProps(preProps);
    const WrappedPre = useCallbackRef((props) => (_jsx(Pre, { ...getPreProps(props) })));
    const getCodeProps = withDefaultProps(codeProps);
    const WrappedCode = useCallbackRef((props) => (_jsx(Code, { ...getCodeProps(props) })));
    const language = /language-(\w+)/.exec(codeProps.className || "")?.[1] ?? "";
    // if the code content is not string (due to rehype plugins), return a default code block
    if (typeof children !== "string") {
        return (_jsx(DefaultCodeBlockContent, { node: node, components: { Pre: WrappedPre, Code: WrappedCode }, code: children }));
    }
    const SyntaxHighlighter = componentsByLanguage[language]?.SyntaxHighlighter ??
        FallbackSyntaxHighlighter;
    const CodeHeader = componentsByLanguage[language]?.CodeHeader ?? FallbackCodeHeader;
    return (_jsx(DefaultCodeBlock, { node: node, components: {
            Pre: WrappedPre,
            Code: WrappedCode,
            SyntaxHighlighter,
            CodeHeader,
        }, language: language || "unknown", code: children }));
};
const CodeOverrideImpl = ({ node, components, componentsByLanguage, ...props }) => {
    const isCodeBlock = useIsMarkdownCodeBlock();
    if (!isCodeBlock)
        return _jsx(components.Code, { ...props });
    return (_jsx(CodeBlockOverride, { node: node, components: components, componentsByLanguage: componentsByLanguage, ...props }));
};
export const CodeOverride = memo(CodeOverrideImpl, (prev, next) => {
    const isEqual = prev.components === next.components &&
        prev.componentsByLanguage === next.componentsByLanguage &&
        memoCompareNodes(prev, next);
    return isEqual;
});
//# sourceMappingURL=CodeOverride.js.map