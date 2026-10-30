import { Easing, interpolate, useCurrentFrame } from "remotion";
import { FONT } from "../font";
import { INK_COLOR, Stage, YELLOW } from "./Stage";

export const HookScene = () => {
  const frame = useCurrentFrame();
  const pop = interpolate(frame, [0, 8], [0.9, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const chip = interpolate(frame, [39, 52], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          left: 70,
          right: 70,
          top: 430,
          textAlign: "center",
          fontFamily: FONT,
          color: INK_COLOR,
          scale: String(pop),
        }}
      >
        <div style={{ fontSize: 72, letterSpacing: 2, opacity: chip }}>会社員の厚生年金</div>
        <div style={{ fontSize: 210, lineHeight: 0.95, marginTop: 12 }}>
          9.15
          <span style={{ fontSize: 120 }}>%</span>
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          left: 180,
          right: 180,
          top: 980,
          height: 28,
          backgroundColor: YELLOW,
          scale: `${chip} 1`,
          opacity: chip,
        }}
      />
    </Stage>
  );
};
