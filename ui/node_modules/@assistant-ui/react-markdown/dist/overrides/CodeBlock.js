import { jsx as _jsx, Fragment as _Fragment, jsxs as _jsxs } from "react/jsx-runtime";
import { useMemo } from "react";
import { DefaultCodeBlockContent } from "./defaultComponents.js";
export const DefaultCodeBlock = ({ node, components: { Pre, Code, SyntaxHighlighter, CodeHeader }, language, code, }) => {
    const components = useMemo(() => ({ Pre, Code }), [Pre, Code]);
    const SH = language ? SyntaxHighlighter : DefaultCodeBlockContent;
    return (_jsxs(_Fragment, { children: [_jsx(CodeHeader, { node: node, language: language, code: code }), _jsx(SH, { node: node, components: components, language: language ?? "unknown", code: code })] }));
};
//# sourceMappingURL=CodeBlock.js.map