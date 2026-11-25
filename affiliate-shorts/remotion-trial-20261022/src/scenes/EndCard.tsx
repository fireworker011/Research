import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT } from "../font";

export const EndCard = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const stamp = interpolate(frame, [0, 0.35 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const line = interpolate(frame, [0.25 * fps, 0.7 * fps], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "#140E08",
        overflow: "hidden",
        fontFamily: FONT,
      }}
    >
      <div
        style={{
          position: "absolute",
          top: 150,
          right: 80,
          backgroundColor: "#E8C872",
          color: "#2A1C08",
          fontSize: 52,
          padding: "12px 26px",
          opacity: stamp,
          rotate: "-8deg",
        }}
      >
        #PR
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          top: 760,
          textAlign: "center",
          color: "#F6E7C1",
          fontSize: 64,
          lineHeight: 1.4,
          opacity: line,
          translate: `0px ${(1 - line) * 24}px`,
        }}
      >
        PR｜広告を含みます
      </div>
    </div>
  );
};
