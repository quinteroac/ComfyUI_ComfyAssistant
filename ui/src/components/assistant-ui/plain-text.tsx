import { MessagePrimitive } from "@assistant-ui/react";
import { type FC } from "react";

// Componente que renderiza cada parte de texto inline
export const PlainText: FC = () => {
  return (
    <span style={{
      display: "inline",
      whiteSpace: "pre-wrap",
      wordBreak: "normal",
      overflowWrap: "break-word"
    }}>
      <MessagePrimitive.Content />
    </span>
  );
};
