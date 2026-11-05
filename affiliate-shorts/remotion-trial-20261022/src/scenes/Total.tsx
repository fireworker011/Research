import { Easing, interpolate, useCurrentFrame } from "remotion";
import { FONT } from "../font";
import { INK_COLOR, Stage, YELLOW } from "./Stage";

export const TotalScene = () => {
  const frame = useCurrentFrame();
  const pop = interpolate(frame, [0, 10], [0.86, 1], {
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
          top: 420,
          textAlign: "center",
          fontFamily: FONT,
          color: INK_COLOR,
          scale: String(pop),
        }}
      >
        <div style={{ fontSize: 64 }}>合わせて</div>
        <div style={{ fontSize: 200, lineHeight: 0.95, marginTop: 8 }}>
          18.3
          <span style={{ fontSize: 110 }}>%</span>
        </div>
        <div
          style={{
            margin: "28px auto 0",
            width: 280,
            height: 22,
            backgroundColor: YELLOW,
          }}
        />
      </div>
    </Stage>
  );
};
