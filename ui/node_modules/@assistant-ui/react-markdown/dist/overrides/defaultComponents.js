import { jsx as _jsx } from "react/jsx-runtime";
export const DefaultPre = ({ node, ...rest }) => (_jsx("pre", { ...rest }));
export const DefaultCode = ({ node, ...rest }) => (_jsx("code", { ...rest }));
export const DefaultCodeBlockContent = ({ node, components: { Pre, Code }, code }) => (_jsx(Pre, { children: _jsx(Code, { node: node, children: code }) }));
export const DefaultCodeHeader = () => null;
//# sourceMappingURL=defaultComponents.js.map