import { Audio } from "@remotion/media";
import { AbsoluteFill, Series, staticFile, useVideoConfig } from "remotion";
import { PensionAge } from "./pension/Age";
import { PensionBirth } from "./pension/Birth";
import { PensionClaim } from "./pension/Claim";
import { PensionEarlier } from "./pension/Earlier";
import { PensionHook } from "./pension/Hook";
import { PensionName } from "./pension/Name";
import { PensionSince } from "./pension/Since";
import { PensionYears } from "./pension/Years";

export const PensionVideo = () => {
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill>
      <Series>
        <Series.Sequence durationInFrames={35} premountFor={fps} name="Hook">
          <PensionHook />
        </Series.Sequence>
        <Series.Sequence durationInFrames={62} premountFor={fps} name="Age">
          <PensionAge />
        </Series.Sequence>
        <Series.Sequence durationInFrames={35} premountFor={fps} name="Name">
          <PensionName />
        </Series.Sequence>
        <Series.Sequence durationInFrames={67} premountFor={fps} name="Birth">
          <PensionBirth />
        </Series.Sequence>
        <Series.Sequence durationInFrames={73} premountFor={fps} name="Years">
          <PensionYears />
        </Series.Sequence>
        <Series.Sequence durationInFrames={52} premountFor={fps} name="Claim">
          <PensionClaim />
        </Series.Sequence>
        <Series.Sequence durationInFrames={111} premountFor={fps} name="Earlier">
          <PensionEarlier />
        </Series.Sequence>
        <Series.Sequence durationInFrames={92} premountFor={fps} name="Since">
          <PensionSince />
        </Series.Sequence>
      </Series>
      <Audio src={staticFile("narration-pension.wav")} />
      <Audio src={staticFile("bgm-pension.wav")} />
    </AbsoluteFill>
  );
};
