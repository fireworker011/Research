import { Easing, interpolate, useCurrentFrame } from "remotion";
import { LINE } from "./theme";

const clockAngle = (hour: number) => (hour / 12) * Math.PI * 2 - Math.PI / 2;

export const ClockFace = ({
  cx,
  cy,
  r,
  drawFrames,
  eveningArc,
}: {
  cx: number;
  cy: number;
  r: number;
  drawFrames: number;
  eveningArc?: boolean;
}) => {
  const frame = useCurrentFrame();
  const circumference = 2 * Math.PI * r;
  const draw =
    drawFrames <= 0
      ? 1
      : interpolate(frame, [0, drawFrames], [0, 1], {
          extrapolateLeft: "clamp",
          extrapolateRight: "clamp",
          easing: Easing.out(Easing.cubic),
        });
  const dashOffset = circumference * (1 - draw);
  const stroke = 8 + Math.sin(frame / 11) * 1.6;
  const innerR = r * (0.84 + Math.sin(frame / 19) * 0.012);
  const tickOpacity = draw * (0.72 + Math.sin(frame / 17) * 0.12);

  const ticks = Array.from({ length: 12 }, (_, index) => {
    const angle = clockAngle(index);
    const inner = r - 26;
    const outer = r - 10;
    return {
      x1: cx + inner * Math.cos(angle),
      y1: cy + inner * Math.sin(angle),
      x2: cx + outer * Math.cos(angle),
      y2: cy + outer * Math.sin(angle),
    };
  });

  const arcR = r + 34;
  const arcStart = clockAngle(4);
  const arcEnd = clockAngle(7);
  const arc = `M ${cx + arcR * Math.cos(arcStart)} ${cy + arcR * Math.sin(arcStart)} A ${arcR} ${arcR} 0 0 1 ${cx + arcR * Math.cos(arcEnd)} ${cy + arcR * Math.sin(arcEnd)}`;

  return (
    <svg
      width={1080}
      height={1920}
      viewBox="0 0 1080 1920"
      style={{ position: "absolute", inset: 0 }}
    >
      <circle
        cx={cx}
        cy={cy}
        r={r}
        fill="none"
        stroke={LINE}
        strokeWidth={stroke}
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={dashOffset}
        transform={`rotate(-90 ${cx} ${cy})`}
      />
      <circle
        cx={cx}
        cy={cy}
        r={innerR}
        fill="none"
        stroke={LINE}
        strokeWidth={2.5}
        opacity={draw * (0.28 + Math.sin(frame / 15) * 0.08)}
      />
      {ticks.map((tick) => (
        <line
          key={`${tick.x1}-${tick.y1}`}
          x1={tick.x1}
          y1={tick.y1}
          x2={tick.x2}
          y2={tick.y2}
          stroke={LINE}
          strokeWidth={4}
          strokeLinecap="round"
          opacity={tickOpacity}
        />
      ))}
      {eveningArc ? (
        <path
          d={arc}
          fill="none"
          stroke={LINE}
          strokeWidth={16 + Math.sin(frame / 13) * 2}
          strokeLinecap="round"
          opacity={0.9}
        />
      ) : null}
    </svg>
  );
};
