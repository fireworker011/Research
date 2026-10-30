import { Easing, interpolate, useCurrentFrame } from "remotion";
import { ClockFace } from "./ClockFace";
import { Field } from "./Field";
import { At, Plate } from "./Plate";
import { LINE } from "./theme";

export const ExampleScene = () => {
  const frame = useCurrentFrame();
  const ringR = 58;
  const circumference = 2 * Math.PI * ringR;
  const half = interpolate(frame, [8, 46], [circumference, circumference / 2], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const breathe = 2 + Math.sin(frame / 12) * 0.8;

  return (
    <Field>
      <ClockFace cx={540} cy={360} r={190} drawFrames={0} />
      <Plate text="5時間" top={600} size={64} />
      <Plate text="例" top={690} size={36} />
      <At text="19時" left={120} top={780} width={280} size={56} />
      <At text="100mg" left={120} top={860} width={280} size={52} />
      <At text="24時" left={680} top={780} width={280} size={56} />
      <At text="50mg" left={680} top={860} width={280} size={52} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <line
          x1={430}
          y1={900}
          x2={620}
          y2={900}
          stroke={LINE}
          strokeWidth={6}
          strokeLinecap="round"
        />
        <polygon points="620,888 648,900 620,912" fill={LINE} />
        <circle
          cx={260}
          cy={1040}
          r={ringR}
          fill="none"
          stroke={LINE}
          strokeWidth={8 + breathe * 0.4}
        />
        <circle
          cx={820}
          cy={1040}
          r={ringR}
          fill="none"
          stroke={LINE}
          strokeWidth={8 + breathe * 0.4}
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={half}
          transform="rotate(-90 820 1040)"
        />
      </svg>
      <Plate text="睡眠ガイド2023" top={1160} size={32} />
    </Field>
  );
};
