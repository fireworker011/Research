import { interpolate } from "remotion";
import { Caption } from "./Caption";
import { GapFigure, OpeningFigure } from "./figures";
import { BED_END, NECK_END, OPEN_END, PILLOW_RX, PILLOW_RY } from "./theme";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

export const Opening = ({ frame }: { frame: number }) => {
  return <OpeningFigure frame={frame} />;
};

export const Neck = ({ frame }: { frame: number }) => {
  const local = frame - OPEN_END;
  const enter = interpolate(local, [0, 60], [0, 1], clamp);
  const gap =
    local < 120
      ? interpolate(local, [0, 50], [0.28, 0.46], clamp)
      : 0.46 + Math.sin((local - 120) / 28) * 0.08;
  const bracket = interpolate(local, [120, 148], [0, 1], clamp);
  const neckLabel = interpolate(local, [8, 22], [0, 1], clamp);
  const numbers = interpolate(local, [120, 142], [0, 1], clamp);

  return (
    <>
      <GapFigure
        frame={frame}
        gap={gap}
        sag={0}
        enter={enter}
        slide={Math.sin(local / 48) * 4}
        bracket={bracket}
        mattressOpacity={interpolate(local, [0, 12], [0.75, 1], clamp)}
        archOpacity={interpolate(local, [0, 16], [0, 1], clamp)}
        pillowRx={PILLOW_RX}
        pillowRy={PILLOW_RY}
      />
      <Caption text="首" top={1160} size={72} opacity={neckLabel} />
      <Caption text="1〜6 cm" top={1290} size={80} opacity={numbers} />
    </>
  );
};

export const Lumbar = ({ frame }: { frame: number }) => {
  const local = frame - NECK_END;
  const growing = interpolate(local, [120, 168], [0.18, 0.9], clamp);
  const gap = local < 120 ? 0.18 : growing;
  const low = interpolate(local, [6, 18], [0, 1], clamp) * interpolate(local, [108, 118], [1, 0], clamp);
  const high = interpolate(local, [124, 142], [0, 1], clamp);
  const waist = interpolate(local, [4, 16], [0, 1], clamp);

  return (
    <>
      <GapFigure
        frame={frame}
        gap={gap}
        sag={0}
        enter={1}
        slide={Math.sin(local / 48) * 4}
        bracket={interpolate(local, [4, 20], [0, 1], clamp)}
        mattressOpacity={1}
        archOpacity={1}
        pillowRx={PILLOW_RX}
        pillowRy={PILLOW_RY}
      />
      <Caption text="腰" top={1120} size={68} opacity={waist} />
      <Caption text="2〜3 cm" top={1248} size={78} opacity={low} />
      <Caption text="4〜6 cm" top={1248} size={78} opacity={high} />
      <Caption text="寝" top={1404} size={56} opacity={low} />
      <Caption text="立" top={1404} size={56} opacity={high} />
    </>
  );
};

export const Bedding = ({ frame }: { frame: number }) => {
  const local = frame - 720;
  const sag =
    local < 120
      ? interpolate(local, [0, 52], [0.12, 1], clamp)
      : interpolate(local, [120, 155], [1, 0], clamp);
  const soft = interpolate(local, [4, 16], [0, 1], clamp) * interpolate(local, [112, 122], [1, 0], clamp);
  const hard =
    interpolate(local, [160, 176], [0, 1], clamp) * interpolate(local, [198, 228], [1, 0], clamp);
  const slideAmp = local < 180 ? 8 : 8 + ((local - 180) / 60) * 30;

  return (
    <>
      <GapFigure
        frame={frame}
        gap={0.5}
        sag={sag}
        enter={1}
        slide={Math.sin(frame / 16) * slideAmp}
        bracket={0}
        mattressOpacity={1}
        archOpacity={0.95}
        pillowRx={PILLOW_RX}
        pillowRy={PILLOW_RY}
      />
      <Caption text="柔" top={1240} size={76} opacity={soft} />
      <Caption text="硬" top={1240} size={76} opacity={hard} />
    </>
  );
};

export const Note = ({ frame }: { frame: number }) => {
  const local = frame - BED_END;
  return (
    <GapFigure
      frame={frame}
      gap={0.5}
      sag={0}
      enter={1}
      slide={Math.sin(frame / 16) * (34 + local * 0.08)}
      bracket={0}
      mattressOpacity={1}
      archOpacity={0.95}
      pillowRx={PILLOW_RX}
      pillowRy={PILLOW_RY}
    />
  );
};
