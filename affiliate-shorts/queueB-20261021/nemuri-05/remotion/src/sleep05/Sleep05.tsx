import { AbsoluteFill, useCurrentFrame } from "remotion";
import { Band } from "./Band";
import { decolFamily } from "./font";
import { Stage } from "./Stage";
import { NAVY } from "./theme";

export const Sleep05 = () => {
  const frame = useCurrentFrame();
  const zoom = 1 + frame * 0.00006;
  return (
    <AbsoluteFill style={{ backgroundColor: NAVY, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          transform: `scale(${zoom})`,
          transformOrigin: "540px 780px",
        }}
      >
        <Band frame={frame} fontFamily={decolFamily} />
        <Stage frame={frame} fontFamily={decolFamily} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
