import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Kiwi Maru";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/kiwi-maru-500.woff2"),
  weight: "500",
});

const ripples = [
  { id: "ripple-1", delay: 0.25 },
  { id: "ripple-2", delay: 0.45 },
  { id: "ripple-3", delay: 0.65 },
] as const;

/** 美容: 雫が落ちて波紋が広がる。 */
export const BeautyRipple: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#F4EEF8",
        backgroundImage: "linear-gradient(180deg, #F7F4FB 0%, #E4D7F2 100%)",
        overflow: "hidden",
        fontFamily,
        fontWeight: 500,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 508,
          top: interpolate(frame, [0, 0.28 * fps], [180, 760], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.in(Easing.quad),
          }),
          width: 64,
          height: 84,
          borderRadius: "50% 50% 50% 50%",
          backgroundColor: "#7E6AA8",
          opacity: interpolate(frame, [0, 0.22 * fps, 0.32 * fps], [1, 1, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          scale: interpolate(frame, [0.22 * fps, 0.34 * fps], [1, 0.3], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            output: "perceptual-scale",
          }),
        }}
      />
      {ripples.map((ripple) => (
        <div
          key={ripple.id}
          style={{
            position: "absolute",
            left: 240,
            top: 620,
            width: 600,
            height: 360,
            borderRadius: "50%",
            border: "6px solid #7E6AA8",
            opacity: interpolate(frame, [ripple.delay * fps, (ripple.delay + 0.7) * fps], [0.8, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
            scale: interpolate(frame, [ripple.delay * fps, (ripple.delay + 0.7) * fps], [0.2, 1.8], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              output: "perceptual-scale",
            }),
          }}
        />
      ))}
      <div
        style={{
          position: "absolute",
          left: 150,
          top: 1080,
          width: 780,
          textAlign: "center",
          color: "#43345F",
          fontFamily,
          fontSize: 86,
          lineHeight: 1.4,
          whiteSpace: "pre-wrap",
          textWrap: "balance",
          opacity: interpolate(frame, [0.4 * fps, 0.8 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {line}
      </div>
      <div
        style={{
          position: "absolute",
          left: 150,
          top: 1560,
          backgroundColor: "#7E6AA8",
          color: "#F8F4FC",
          fontFamily,
          fontSize: 48,
          padding: "10px 26px",
          borderRadius: 999,
          opacity: interpolate(frame, [0.6 * fps, 0.9 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        {prLabel}
      </div>
    </AbsoluteFill>
  );
};

export const BeautyRippleComposition = () => {
  return (
    <Composition
      id="BeautyRipple"
      component={BeautyRipple}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "乾く前に、手元を見て",
        prLabel: "#PR",
      }}
    />
  );
};
