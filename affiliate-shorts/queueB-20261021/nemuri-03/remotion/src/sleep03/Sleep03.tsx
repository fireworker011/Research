import { AbsoluteFill, Series } from "remotion";
import { ExampleScene } from "./ExampleScene";
import { HalfLifeScene } from "./HalfLifeScene";
import { LimitScene } from "./LimitScene";
import { OpeningScene } from "./OpeningScene";
import { BG, CUT } from "./theme";

export const Sleep03 = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: BG }}>
      <Series>
        <Series.Sequence durationInFrames={CUT} name="Open" premountFor={0}>
          <OpeningScene />
        </Series.Sequence>
        <Series.Sequence durationInFrames={CUT} name="Half" premountFor={0}>
          <HalfLifeScene />
        </Series.Sequence>
        <Series.Sequence durationInFrames={CUT} name="Example" premountFor={0}>
          <ExampleScene />
        </Series.Sequence>
        <Series.Sequence durationInFrames={CUT} name="Limit" premountFor={0}>
          <LimitScene />
        </Series.Sequence>
      </Series>
    </AbsoluteFill>
  );
};
