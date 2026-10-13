import { Composition } from "remotion";
import { Film } from "./Film";
import { SERUM_DURATION, SERUM_FPS, SERUM_HEIGHT, SERUM_WIDTH, SerumFilm } from "./orbis/SerumFilm";
import { PaperFilm } from "./PaperFilm";
import {
  PAPER_DURATION,
  PAPER_FPS,
  PAPER_HEIGHT,
  PAPER_WIDTH,
} from "./paper/timing";
import { DURATION, FPS, HEIGHT, WIDTH } from "./theme";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="CodeVideo"
        component={Film}
        durationInFrames={DURATION}
        fps={FPS}
        width={WIDTH}
        height={HEIGHT}
      />
      <Composition
        id="PaperThread"
        component={PaperFilm}
        durationInFrames={PAPER_DURATION}
        fps={PAPER_FPS}
        width={PAPER_WIDTH}
        height={PAPER_HEIGHT}
      />
      <Composition
        id="OrbisSerum"
        component={SerumFilm}
        durationInFrames={SERUM_DURATION}
        fps={SERUM_FPS}
        width={SERUM_WIDTH}
        height={SERUM_HEIGHT}
      />
    </>
  );
};
