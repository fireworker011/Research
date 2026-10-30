import { INK } from "./theme";
import { kleeFamily } from "./font";

export const Caption = ({
  text,
  top,
  size,
  opacity,
}: {
  text: string;
  top: number;
  size: number;
  opacity: number;
}) => {
  return (
    <div
      style={{
        position: "absolute",
        left: 70,
        width: 940,
        top,
        opacity,
        textAlign: "center",
        fontFamily: kleeFamily,
        fontWeight: 600,
        fontSize: size,
        color: INK,
        lineHeight: 1.15,
        letterSpacing: "0.02em",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};
