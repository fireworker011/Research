import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Noto Sans JP";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/noto-sans-jp-700.woff2"),
  weight: "700",
});

const stars = [
  { id: "s1", left: 120, top: 180, size: 10, peaks: [0.2, 1, 0.35, 0.9] },
  { id: "s2", left: 260, top: 320, size: 6, peaks: [1, 0.25, 0.85, 0.3] },
  { id: "s3", left: 180, top: 520, size: 8, peaks: [0.4, 0.95, 0.2, 0.8] },
  { id: "s4", left: 420, top: 160, size: 7, peaks: [0.7, 0.2, 1, 0.4] },
  { id: "s5", left: 90, top: 760, size: 5, peaks: [0.3, 0.8, 0.25, 1] },
] as const;

/** 睡眠: 月がゆっくり流れて星が瞬く。 */
export const SleepMoon: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        fontFamily,
        fontWeight: 700,
        backgroundImage: "linear-gradient(180deg, #0C1228 0%, #243256 72%, #070B16 72%)",
      }}
    >
      <div
        style={{
          position: "absolute",
          width: 280,
          height: 280,
          borderRadius: 140,
          backgroundColor: "#F4E7C8",
          boxShadow: "0 0 80px rgba(244,231,200,0.45)",
          translate: interpolate(frame, [0, 2 * fps], ["760px 180px", "640px 120px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          width: 240,
          height: 240,
          borderRadius: 120,
          backgroundColor: "#1A2744",
          translate: interpolate(frame, [0, 2 * fps], ["820px 150px", "710px 90px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          }),
        }}
      />
      {stars.map((star) => (
        <div
          key={star.id}
          style={{
            position: "absolute",
            left: star.left,
            top: star.top,
            width: star.size,
            height: star.size,
            borderRadius: star.size,
            backgroundColor: "#F4F0E4",
            opacity: interpolate(frame, [0, 0.5 * fps, 1 * fps, 1.5 * fps, 2 * fps], [star.peaks[0], star.peaks[1], star.peaks[2], star.peaks[3], star.peaks[0]], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        />
      ))}
      <div
        style={{
          position: "absolute",
          right: 100,
          top: 160,
          color: "#C9C3DC",
          fontFamily,
          fontWeight: 700,
          fontSize: 48,
          opacity: interpolate(frame, [0.2 * fps, 0.6 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {prLabel}
      </div>
      <div
        style={{
          position: "absolute",
          left: 100,
          top: 960,
          width: 820,
          textAlign: "left",
          color: "#E7E2F4",
          fontFamily,
          fontWeight: 700,
          fontSize: 84,
          lineHeight: 1.4,
          whiteSpace: "pre-wrap",
          opacity: interpolate(frame, [0.3 * fps, 0.9 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.33, 0, 0.2, 1),
          }),
        }}
      >
        {line}
      </div>
    </AbsoluteFill>
  );
};

export const SleepMoonComposition = () => {
  return (
    <Composition
      id="SleepMoon"
      component={SleepMoon}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "枕元の明るさ、落としてみて",
        prLabel: "#PR",
      }}
    />
  );
};
