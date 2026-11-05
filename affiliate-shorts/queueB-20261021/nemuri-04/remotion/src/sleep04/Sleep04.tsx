import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Bedding, Lumbar, Neck, Note, Opening } from "./scenes";
import { BED_END, BG, LUMBAR_END, NECK_END, OPEN_END } from "./theme";

export const Sleep04 = () => {
  const frame = useCurrentFrame();
  return (
    <AbsoluteFill style={{ backgroundColor: BG, overflow: "hidden" }}>
      {frame < OPEN_END ? <Opening frame={frame} /> : null}
      {frame >= OPEN_END && frame < NECK_END ? <Neck frame={frame} /> : null}
      {frame >= NECK_END && frame < LUMBAR_END ? <Lumbar frame={frame} /> : null}
      {frame >= LUMBAR_END && frame < BED_END ? <Bedding frame={frame} /> : null}
      {frame >= BED_END ? <Note frame={frame} /> : null}
    </AbsoluteFill>
  );
};
