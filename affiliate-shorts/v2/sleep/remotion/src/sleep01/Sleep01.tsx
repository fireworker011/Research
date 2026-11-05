import { Series, useVideoConfig } from "remotion";
import { AimScene } from "./AimScene";
import { DisclaimerScene } from "./DisclaimerScene";
import { HookScene } from "./HookScene";
import { PrScene } from "./PrScene";
import { RangeScene } from "./RangeScene";
import { SurveyScene } from "./SurveyScene";

export const Sleep01 = () => {
  const { fps } = useVideoConfig();

  return (
    <Series>
      <Series.Sequence name="Hook" durationInFrames={120} premountFor={fps}>
        <HookScene />
      </Series.Sequence>
      <Series.Sequence name="Aim" durationInFrames={150} premountFor={fps}>
        <AimScene />
      </Series.Sequence>
      <Series.Sequence name="Range" durationInFrames={150} premountFor={fps}>
        <RangeScene />
      </Series.Sequence>
      <Series.Sequence name="Survey" durationInFrames={210} premountFor={fps}>
        <SurveyScene />
      </Series.Sequence>
      <Series.Sequence name="Disclaimer" durationInFrames={90} premountFor={fps}>
        <DisclaimerScene />
      </Series.Sequence>
      <Series.Sequence name="PR" durationInFrames={60} premountFor={fps}>
        <PrScene />
      </Series.Sequence>
    </Series>
  );
};
