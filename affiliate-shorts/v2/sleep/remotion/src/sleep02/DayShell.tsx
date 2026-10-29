import type { ReactNode } from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { sansFamily } from "../sans";

export const DayShell = ({ children }: { children: ReactNode }) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#F6E6D2", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          bottom: 0,
          width: 28,
          backgroundColor: "#E23D12",
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          bottom: 0,
          width: 160,
          backgroundColor: "#E23D12",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 118,
          left: 96,
          fontFamily: sansFamily,
          fontWeight: 900,
          fontSize: 44,
          color: "#1A120C",
        }}
      >
        ねむりの棚
      </div>
      <div
        style={{
          position: "absolute",
          left: 96,
          width: 180,
          top: 184,
          height: 10,
          backgroundColor: "#E23D12",
          scale: interpolate(frame, [0, 8], [0.05, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.2, 0.8, 0.2, 1),
            output: "perceptual-scale",
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 96,
          right: 184,
          top: 230,
          bottom: 140,
          display: "flex",
          justifyContent: "center",
          alignItems: "flex-start",
          opacity: interpolate(frame, [0, 5], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          translate: interpolate(frame, [0, 6], ["-72px 0px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "flex-start",
            gap: 14,
          }}
        >
          {children}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const SansLine = ({
  text,
  size,
  color,
  weight = 900,
}: {
  text: string;
  size: number;
  color: string;
  weight?: 400 | 700 | 900;
}) => {
  return (
    <div
      style={{
        fontFamily: sansFamily,
        fontSize: size,
        fontWeight: weight,
        color,
        lineHeight: 1.15,
        textAlign: "left",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};
