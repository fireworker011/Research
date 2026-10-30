import { interpolate } from "remotion";
import { GOLD, INK, NAVY, clamp } from "./theme";

const heading = (frame: number) => {
  if (frame < 60) {
    return "朝";
  }
  if (frame < 210) {
    return "日中";
  }
  if (frame < 360) {
    return "寝室";
  }
  if (frame < 510) {
    return "入浴";
  }
  return "";
};

const wavePath = (frame: number, width: number) => {
  const base = 688;
  const steps = 24;
  let path = `M 0 0 L ${width.toFixed(1)} 0 L ${width.toFixed(1)} ${base}`;
  for (let i = steps; i >= 0; i--) {
    const x = (width * i) / steps;
    const y = base + Math.sin(frame / 12 + i * 0.55) * 14;
    path += ` L ${x.toFixed(1)} ${y.toFixed(1)}`;
  }
  return `${path} Z`;
};

const waveLine = (frame: number, width: number) => {
  const base = 688;
  const steps = 24;
  let path = "";
  for (let i = 0; i <= steps; i++) {
    const x = (width * i) / steps;
    const y = base + Math.sin(frame / 12 + i * 0.55) * 14;
    path += `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)} `;
  }
  return path;
};

export const Band = ({ frame, fontFamily }: { frame: number; fontFamily: string }) => {
  const width = interpolate(frame, [0, 36], [0, 1080], clamp);
  const text = heading(frame);
  const born = interpolate(frame, [30, 44], [0, 1], clamp);
  const fadeOut = interpolate(frame, [496, 510], [1, 0], clamp);
  const opacity = text === "" ? 0 : Math.min(born, fadeOut);

  return (
    <>
      {width > 1 ? (
        <svg
          width={1080}
          height={1920}
          viewBox="0 0 1080 1920"
          style={{ position: "absolute", inset: 0 }}
        >
          <path d={wavePath(frame, width)} fill={GOLD} />
          <path
            d={waveLine(frame, width)}
            fill="none"
            stroke={INK}
            strokeWidth={3 + Math.sin(frame / 13) * 1.2}
            strokeLinejoin="round"
          />
        </svg>
      ) : null}
      {opacity > 0.02 ? (
        <div
          style={{
            position: "absolute",
            left: 230,
            top: 228,
            width: 620,
            height: 200,
            borderRadius: 40,
            backgroundColor: NAVY,
            opacity,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            fontFamily,
            fontWeight: 700,
            fontSize: 108,
            lineHeight: 1,
            color: INK,
            whiteSpace: "nowrap",
          }}
        >
          {text}
        </div>
      ) : null}
    </>
  );
};
