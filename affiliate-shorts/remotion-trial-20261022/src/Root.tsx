import { Composition, Folder } from "remotion";
import { RateVideo } from "./RateVideo";
import { EndCard } from "./scenes/EndCard";
import { FixedScene } from "./scenes/Fixed";
import { FormulaScene } from "./scenes/Formula";
import { HookScene } from "./scenes/Hook";
import { SplitScene } from "./scenes/Split";
import { TotalScene } from "./scenes/Total";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="PensionRate"
        component={RateVideo}
        durationInFrames={426}
        fps={30}
        width={1080}
        height={1920}
      />
      <Folder name="Scenes">
        <Composition
          id="Hook"
          component={HookScene}
          durationInFrames={118}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="Split"
          component={SplitScene}
          durationInFrames={51}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="Total"
          component={TotalScene}
          durationInFrames={63}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="Formula"
          component={FormulaScene}
          durationInFrames={59}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="Fixed"
          component={FixedScene}
          durationInFrames={75}
          fps={30}
          width={1080}
          height={1920}
        />
        <Composition
          id="EndCard"
          component={EndCard}
          durationInFrames={60}
          fps={30}
          width={1080}
          height={1920}
        />
      </Folder>
    </>
  );
};
