import { interpolate, useCurrentFrame } from "remotion";
import { ClockFace } from "./ClockFace";
import { Field } from "./Field";
import { Plate } from "./Plate";

export const OpeningScene = () => {
  const frame = useCurrentFrame();
  const titleOpacity = interpolate(frame, [54, 72], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <Field>
      <ClockFace cx={540} cy={640} r={300} drawFrames={48} />
      <Plate text="夕方の一杯、残る？" top={1040} size={68} opacity={titleOpacity} />
    </Field>
  );
};
