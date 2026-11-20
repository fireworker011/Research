import type { ReactNode } from "react";
import { AbsoluteFill, interpolate, staticFile, useCurrentFrame } from "remotion";
import { mono, sans } from "../fonts";

export const Paper = ({
  children,
  background = "#f3efe8",
  grain = true,
}: {
  children: ReactNode;
  background?: string;
  grain?: boolean;
}) => {
  return (
    <AbsoluteFill style={{ background }}>
      {grain ? (
        <AbsoluteFill
          style={{
            backgroundImage: `url(${staticFile("paper-noise.png")})`,
            backgroundSize: "256px 256px",
            opacity: 0.4,
            mixBlendMode: "multiply",
          }}
        />
      ) : null}
      {children}
    </AbsoluteFill>
  );
};

export const Caption = ({
  text,
  color = "#2a2a2a",
  bottom = 72,
}: {
  text: string;
  color?: string;
  bottom?: number;
}) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [10, 24], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 80,
        right: 80,
        bottom,
        textAlign: "center",
        fontFamily: sans,
        fontWeight: 500,
        fontSize: 30,
        letterSpacing: "0.12em",
        color,
        opacity,
      }}
    >
      {text}
    </div>
  );
};

export const Fig = ({ n, title }: { n: string; title: string }) => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [6, 18], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 56,
        left: 64,
        zIndex: 2,
        fontFamily: mono,
        fontSize: 18,
        lineHeight: 1.5,
        letterSpacing: "0.06em",
        color: "#6a675f",
        opacity,
      }}
    >
      <div>FIG. {n}</div>
      <div>{title}</div>
    </div>
  );
};
