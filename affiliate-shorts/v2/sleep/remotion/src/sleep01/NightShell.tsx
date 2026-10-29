import type { ReactNode } from "react";
import { AbsoluteFill, Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { serifFamily } from "../serif";

export const NightShell = ({ children }: { children: ReactNode }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#070B18", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          left: 640,
          top: 230,
          width: 300,
          height: 300,
          translate: interpolate(frame, [0, 3 * fps], ["0px 0px", "0px 36px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div
          style={{
            position: "absolute",
            width: 250,
            height: 250,
            borderRadius: 125,
            backgroundColor: "#E7E1D4",
            opacity: 0.9,
          }}
        />
        <div
          style={{
            position: "absolute",
            width: 210,
            height: 210,
            borderRadius: 105,
            backgroundColor: "#070B18",
            left: 58,
            top: -18,
          }}
        />
      </div>
      <div
        style={{
          position: "absolute",
          top: 118,
          left: 80,
          right: 80,
          textAlign: "center",
          fontFamily: serifFamily,
          fontWeight: 400,
          fontSize: 44,
          color: "#9AA6C8",
        }}
      >
        ねむりの棚
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          top: 220,
          bottom: 140,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          opacity: interpolate(frame, [0, 0.7 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [0, 0.7 * fps], ["0px 36px", "0px 0px"], {
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
            alignItems: "center",
            gap: 22,
          }}
        >
          {children}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const SerifLine = ({
  text,
  size,
  color,
  weight = 700,
}: {
  text: string;
  size: number;
  color: string;
  weight?: 400 | 700;
}) => {
  return (
    <div
      style={{
        fontFamily: serifFamily,
        fontSize: size,
        fontWeight: weight,
        color,
        lineHeight: 1.2,
        textAlign: "center",
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};
