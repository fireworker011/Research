import { Composition } from "remotion";
import { Film } from "./Film";
import { DURATION, FPS, HEIGHT, WIDTH } from "./theme";

export const RemotionRoot = () => {
  return (
    <Composition
      id="CodeVideo"
      component={Film}
      durationInFrames={DURATION}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  );
};
