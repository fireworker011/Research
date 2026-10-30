import { Audio } from "@remotion/media";
import { AbsoluteFill, Series, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { Caption } from "./Caption";
import { CARD_FRAME } from "./lines";
import { EndCard } from "./scenes/EndCard";
import { FixedScene } from "./scenes/Fixed";
import { FormulaScene } from "./scenes/Formula";
import { HookScene } from "./scenes/Hook";
import { SplitScene } from "./scenes/Split";
import { TotalScene } from "./scenes/Total";

export const RateVideo = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#F7F1E6" }}>
      <Series>
        <Series.Sequence durationInFrames={118} premountFor={fps} name="Hook">
          <HookScene />
        </Series.Sequence>
        <Series.Sequence durationInFrames={51} premountFor={fps} name="Split">
          <SplitScene />
        </Series.Sequence>
        <Series.Sequence durationInFrames={63} premountFor={fps} name="Total">
          <TotalScene />
        </Series.Sequence>
        <Series.Sequence durationInFrames={59} premountFor={fps} name="Formula">
          <FormulaScene />
        </Series.Sequence>
        <Series.Sequence durationInFrames={75} premountFor={fps} name="Fixed">
          <FixedScene />
        </Series.Sequence>
        <Series.Sequence durationInFrames={60} premountFor={fps} name="EndCard">
          <EndCard />
        </Series.Sequence>
      </Series>
      {frame < CARD_FRAME ? <Caption /> : null}
      <Audio src={staticFile("narration.wav")} />
      <Audio src={staticFile("bgm.wav")} />
    </AbsoluteFill>
  );
};
