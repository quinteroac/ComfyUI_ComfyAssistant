import classNames from "classnames";
export const withDefaultProps = ({ className, ...defaultProps }) => ({ className: classNameProp, ...props }) => {
    return {
        className: classNames(className, classNameProp),
        ...defaultProps,
        ...props,
    };
};
//# sourceMappingURL=withDefaults.js.map