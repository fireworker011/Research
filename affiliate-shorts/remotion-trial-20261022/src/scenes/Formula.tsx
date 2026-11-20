import { Easing, interpolate, useCurrentFrame } from "remotion";
import { FONT } from "../font";
import { INK_CARD, Stage, YELLOW } from "./Stage";

const Row = ({ label, from }: { label: string; from: number }) => {
  const frame = useCurrentFrame();
  const width = interpolate(frame, [from, from + 16], [0, 520], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div style={{ marginBottom: 36 }}>
      <div style={{ fontFamily: FONT, fontSize: 52, marginBottom: 12 }}>{label}</div>
      <div style={{ height: 36, width, backgroundColor: YELLOW, borderRadius: 8 }} />
      <div style={{ fontFamily: FONT, fontSize: 40, marginTop: 10, color: INK_CARD }}>
        × 18.3%
      </div>
    </div>
  );
};

export const FormulaScene = () => {
  return (
    <Stage>
      <div style={{ position: "absolute", left: 90, right: 90, top: 360 }}>
        <Row label="標準報酬" from={0} />
        <Row label="賞与" from={12} />
      </div>
    </Stage>
  );
};
