import { Easing, interpolate, useCurrentFrame } from "remotion";
import { FONT } from "../font";
import { INK_CARD, Stage, YELLOW } from "./Stage";

const Card = ({
  label,
  from,
}: {
  label: string;
  from: number;
}) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [from, from + 10], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        flex: 1,
        backgroundColor: INK_CARD,
        color: YELLOW,
        borderRadius: 28,
        padding: "36px 12px 42px",
        textAlign: "center",
        fontFamily: FONT,
        opacity: enter,
        translate: `0px ${(1 - enter) * 36}px`,
      }}
    >
      <div style={{ fontSize: 48, color: "#FFF8EC" }}>{label}</div>
      <div style={{ fontSize: 92, lineHeight: 1.05, marginTop: 18 }}>
        9.15
        <span style={{ fontSize: 48 }}>%</span>
      </div>
    </div>
  );
};

export const SplitScene = () => {
  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          left: 64,
          right: 64,
          top: 380,
          display: "flex",
          gap: 24,
        }}
      >
        <Card label="本人" from={0} />
        <Card label="会社" from={6} />
      </div>
    </Stage>
  );
};
