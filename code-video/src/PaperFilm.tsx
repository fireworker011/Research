import { AbsoluteFill, Sequence } from "remotion";
import {
  CityScene,
  DrawScene,
  IslandScene,
  NightScene,
  PairScene,
  PalmScene,
  RedScene,
} from "./paper/scenes";
import {
  CITY_DURATION,
  CITY_FROM,
  DRAW_DURATION,
  DRAW_FROM,
  ISLAND_DURATION,
  ISLAND_FROM,
  NIGHT_DURATION,
  NIGHT_FROM,
  PAIR_DURATION,
  PAIR_FROM,
  PALM_DURATION,
  PALM_FROM,
  RED_DURATION,
  RED_FROM,
} from "./paper/timing";

export const PaperFilm = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#f3efe8" }}>
      <Sequence from={DRAW_FROM} durationInFrames={DRAW_DURATION}>
        <DrawScene />
      </Sequence>
      <Sequence from={RED_FROM} durationInFrames={RED_DURATION}>
        <RedScene />
      </Sequence>
      <Sequence from={ISLAND_FROM} durationInFrames={ISLAND_DURATION}>
        <IslandScene />
      </Sequence>
      <Sequence from={NIGHT_FROM} durationInFrames={NIGHT_DURATION}>
        <NightScene />
      </Sequence>
      <Sequence from={CITY_FROM} durationInFrames={CITY_DURATION}>
        <CityScene />
      </Sequence>
      <Sequence from={PAIR_FROM} durationInFrames={PAIR_DURATION}>
        <PairScene />
      </Sequence>
      <Sequence from={PALM_FROM} durationInFrames={PALM_DURATION}>
        <PalmScene />
      </Sequence>
    </AbsoluteFill>
  );
};
