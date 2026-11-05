import { Easing, interpolate, useCurrentFrame } from "remotion";
import { ClockFace } from "./ClockFace";
import { Field } from "./Field";
import { Plate } from "./Plate";
import { LINE } from "./theme";

export const LimitScene = () => {
  const frame = useCurrentFrame();
  const fill = interpolate(frame, [0, 50], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });
  const barX = 200;
  const barW = 680;
  const shine = (Math.sin(frame / 14) + 1) / 2;
  const noteOpacity = interpolate(frame, [24, 40], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <Field>
      <ClockFace cx={540} cy={390} r={200} drawFrames={0} eveningArc />
      <Plate text="夕方以降" top={680} size={48} />
      <Plate text="1日" top={770} size={36} />
      <Plate text="400mg" top={830} size={88} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <line
          x1={barX}
          y1={1000}
          x2={barX + barW}
          y2={1000}
          stroke={LINE}
          strokeWidth={8}
          strokeLinecap="round"
          opacity={0.45}
        />
        <line
          x1={barX}
          y1={1000}
          x2={barX + barW * fill}
          y2={1000}
          stroke={LINE}
          strokeWidth={14}
          strokeLinecap="round"
        />
        <circle cx={barX + barW * (0.15 + shine * 0.8)} cy={1000} r={11} fill={LINE} />
        <line
          x1={barX + barW}
          y1={972}
          x2={barX + barW}
          y2={1028}
          stroke={LINE}
          strokeWidth={6}
          strokeLinecap="round"
        />
      </svg>
      <Plate text="睡眠ガイド2023" top={1060} size={32} opacity={noteOpacity} />
      <Plate text="医療的な助言ではありません" top={1140} size={36} opacity={noteOpacity} />
    </Field>
  );
};
