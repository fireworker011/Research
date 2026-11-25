import { Easing, interpolate, useCurrentFrame } from "remotion";
import { FONT } from "../font";
import { INK_COLOR, Stage, YELLOW } from "./Stage";

export const FixedScene = () => {
  const frame = useCurrentFrame();
  const line = interpolate(frame, [8, 28], [0, 640], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const stamp = interpolate(frame, [18, 32], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          top: 400,
          textAlign: "center",
          fontFamily: FONT,
          color: INK_COLOR,
        }}
      >
        <div style={{ fontSize: 72 }}>平成29年9月</div>
        <div
          style={{
            margin: "28px auto 0",
            width: line,
            height: 18,
            backgroundColor: YELLOW,
          }}
        />
        <div style={{ fontSize: 84, marginTop: 36, opacity: stamp }}>この率で固定</div>
      </div>
    </Stage>
  );
};
