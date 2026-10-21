import { useCurrentFrame } from "remotion";
import { ClockFace } from "./ClockFace";
import { Field } from "./Field";
import { At, Plate } from "./Plate";
import { LINE } from "./theme";

export const HalfLifeScene = () => {
  const frame = useCurrentFrame();
  const along = (Math.sin(frame / 20) + 1) / 2;
  const dotX = 250 + along * 580;

  return (
    <Field>
      <ClockFace cx={540} cy={400} r={210} drawFrames={0} />
      <Plate text="半減期" top={680} size={52} />
      <At text="3" left={70} top={800} width={150} size={120} />
      <At text="7" left={860} top={800} width={150} size={120} />
      <svg width={1080} height={1920} style={{ position: "absolute", inset: 0 }}>
        <line
          x1={230}
          y1={868}
          x2={850}
          y2={868}
          stroke={LINE}
          strokeWidth={10}
          strokeLinecap="round"
        />
        <circle cx={dotX} cy={868} r={16} fill={LINE} />
      </svg>
      <Plate text="時間" top={960} size={44} />
      <Plate text="個人差" top={1040} size={40} />
      <Plate text="睡眠ガイド2023" top={1140} size={32} />
    </Field>
  );
};
