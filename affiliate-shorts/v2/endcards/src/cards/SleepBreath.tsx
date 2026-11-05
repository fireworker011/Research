import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Yomogi";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/yomogi-400.woff2"),
  weight: "400",
});

const bars = [
  { id: "b1", peak: 140, delay: 0.08 },
  { id: "b2", peak: 220, delay: 0.14 },
  { id: "b3", peak: 320, delay: 0.2 },
  { id: "b4", peak: 400, delay: 0.26 },
  { id: "b5", peak: 320, delay: 0.2 },
  { id: "b6", peak: 220, delay: 0.14 },
  { id: "b7", peak: 140, delay: 0.08 },
] as const;

/** 睡眠: バーが一度ふくらんで静かに戻る。 */
export const SleepBreath: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#E4EEE8", overflow: "hidden", fontFamily, fontWeight: 400 }}>
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 340,
          width: 840,
          textAlign: "center",
          color: "#1E3A32",
          fontFamily,
          fontSize: 84,
          lineHeight: 1.45,
          whiteSpace: "pre-wrap",
          textWrap: "balance",
          opacity: interpolate(frame, [0.15 * fps, 0.7 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.sin),
          }),
        }}
      >
        {line}
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 760,
          textAlign: "center",
          color: "#3E6B5C",
          fontFamily,
          fontSize: 52,
          opacity: interpolate(frame, [0.4 * fps, 0.85 * fps], [0, 1], {
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
          left: 90,
          top: 1180,
          width: 900,
          height: 520,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
        }}
      >
        {bars.map((bar) => (
          <div
            key={bar.id}
            style={{
              width: 78,
              borderRadius: 39,
              backgroundColor: "#7FA894",
              height: interpolate(
                frame,
                [bar.delay * fps, (bar.delay + 0.7) * fps, (bar.delay + 1.25) * fps],
                [80, bar.peak, 120],
                {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                  easing: Easing.inOut(Easing.sin),
                },
              ),
            }}
          />
        ))}
      </div>
    </AbsoluteFill>
  );
};

export const SleepBreathComposition = () => {
  return (
    <Composition
      id="SleepBreath"
      component={SleepBreath}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "同じ時刻に、布団へ入って",
        prLabel: "#PR",
      }}
    />
  );
};
