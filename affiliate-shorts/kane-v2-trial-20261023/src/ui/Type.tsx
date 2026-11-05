import { DISPLAY } from "../font";
import { INK, RED } from "../theme";
import { useEnter } from "./motion";

export const Hero: React.FC<{
  readonly children: React.ReactNode;
  readonly color?: string;
  readonly size?: number;
}> = ({ children, color = RED, size = 128 }) => {
  const scale = useEnter();
  return (
    <div
      style={{
        fontFamily: DISPLAY,
        fontSize: size,
        color,
        lineHeight: 1.05,
        textAlign: "center",
        transform: `scale(${scale})`,
      }}
    >
      {children}
    </div>
  );
};

export const Sub: React.FC<{
  readonly children: React.ReactNode;
  readonly size?: number;
}> = ({ children, size = 52 }) => {
  return (
    <div
      style={{
        fontFamily: DISPLAY,
        fontSize: size,
        color: INK,
        lineHeight: 1.25,
        textAlign: "center",
      }}
    >
      {children}
    </div>
  );
};

export const FactBlock: React.FC<{
  readonly top?: number;
  readonly children: React.ReactNode;
}> = ({ top = 860, children }) => {
  return (
    <div
      style={{
        position: "absolute",
        left: 80,
        right: 80,
        top,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        gap: 16,
      }}
    >
      {children}
    </div>
  );
};
