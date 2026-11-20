import { Series, useVideoConfig } from "remotion";
import { DisclaimerScene } from "./DisclaimerScene";
import { HeatScene } from "./HeatScene";
import { HookScene } from "./HookScene";
import { PrScene } from "./PrScene";
import { SummerScene } from "./SummerScene";
import { WinterScene } from "./WinterScene";

export const Sleep02 = () => {
  const { fps } = useVideoConfig();

  return (
    <Series>
      <Series.Sequence name="Hook" durationInFrames={60} premountFor={fps}>
        <HookScene />
      </Series.Sequence>
      <Series.Sequence name="Heat" durationInFrames={135} premountFor={fps}>
        <HeatScene />
      </Series.Sequence>
      <Series.Sequence name="Summer" durationInFrames={75} premountFor={fps}>
        <SummerScene />
      </Series.Sequence>
      <Series.Sequence name="Winter" durationInFrames={150} premountFor={fps}>
        <WinterScene />
      </Series.Sequence>
      <Series.Sequence name="Disclaimer" durationInFrames={60} premountFor={fps}>
        <DisclaimerScene />
      </Series.Sequence>
      <Series.Sequence name="PR" durationInFrames={60} premountFor={fps}>
        <PrScene />
      </Series.Sequence>
    </Series>
  );
};
