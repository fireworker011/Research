import { Composition, Folder } from "remotion";
import { AimScene } from "./sleep01/AimScene";
import { DisclaimerScene as S01Disclaimer } from "./sleep01/DisclaimerScene";
import { HookScene as S01Hook } from "./sleep01/HookScene";
import { PrScene as S01Pr } from "./sleep01/PrScene";
import { RangeScene } from "./sleep01/RangeScene";
import { Sleep01 } from "./sleep01/Sleep01";
import { SurveyScene } from "./sleep01/SurveyScene";
import { DisclaimerScene as S02Disclaimer } from "./sleep02/DisclaimerScene";
import { HeatScene } from "./sleep02/HeatScene";
import { HookScene as S02Hook } from "./sleep02/HookScene";
import { PrScene as S02Pr } from "./sleep02/PrScene";
import { Sleep02 } from "./sleep02/Sleep02";
import { SummerScene } from "./sleep02/SummerScene";
import { WinterScene } from "./sleep02/WinterScene";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="Sleep01"
        component={Sleep01}
        durationInFrames={780}
        fps={30}
        width={1080}
        height={1920}
      />
      <Composition
        id="Sleep02"
        component={Sleep02}
        durationInFrames={540}
        fps={30}
        width={1080}
        height={1920}
      />
      <Folder name="Sleep01Scenes">
        <Composition
          id="S01Hook"
          component={S01Hook}
          durationInFrames={120}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S01Aim"
          component={AimScene}
          durationInFrames={150}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S01Range"
          component={RangeScene}
          durationInFrames={150}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S01Survey"
          component={SurveyScene}
          durationInFrames={210}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S01Disclaimer"
          component={S01Disclaimer}
          durationInFrames={90}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S01Pr"
          component={S01Pr}
          durationInFrames={60}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>
      <Folder name="Sleep02Scenes">
        <Composition
          id="S02Hook"
          component={S02Hook}
          durationInFrames={60}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S02Heat"
          component={HeatScene}
          durationInFrames={135}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S02Summer"
          component={SummerScene}
          durationInFrames={75}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S02Winter"
          component={WinterScene}
          durationInFrames={150}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S02Disclaimer"
          component={S02Disclaimer}
          durationInFrames={60}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="S02Pr"
          component={S02Pr}
          durationInFrames={60}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>
    </>
  );
};
