import { maruFamily } from "./font";
import { TEXT } from "./theme";

export const Plate = ({
  text,
  top,
  size,
  opacity = 1,
}: {
  text: string;
  top: number;
  size: number;
  opacity?: number;
}) => {
  return (
    <div
      style={{
        position: "absolute",
        left: 60,
        width: 960,
        top,
        textAlign: "center",
        fontFamily: maruFamily,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.15,
        color: TEXT,
        opacity,
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};

export const At = ({
  text,
  left,
  top,
  width,
  size,
  opacity = 1,
}: {
  text: string;
  left: number;
  top: number;
  width: number;
  size: number;
  opacity?: number;
}) => {
  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width,
        textAlign: "center",
        fontFamily: maruFamily,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.15,
        color: TEXT,
        opacity,
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};
