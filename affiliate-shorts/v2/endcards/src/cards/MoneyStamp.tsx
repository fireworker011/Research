import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Shippori Mincho";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/shippori-mincho-700.woff2"),
  weight: "700",
});

/** 金メモ: 金の印が落ちて押される。 */
export const MoneyStamp: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#140E08", overflow: "hidden", fontFamily, fontWeight: 700 }}>
      <AbsoluteFill
        style={{
          background: "radial-gradient(circle at 50% 40%, #3C2E18 0%, #140E08 64%)",
        }}
      />
      <div
        style={{
          position: "absolute",
          top: 128,
          right: 108,
          padding: "12px 26px",
          backgroundColor: "#E8C872",
          color: "#2A1C08",
          fontFamily,
          fontSize: 52,
          fontWeight: 700,
          opacity: interpolate(frame, [0.2 * fps, 0.4 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          rotate: interpolate(frame, [0.2 * fps, 0.55 * fps], ["-16deg", "-8deg"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(1.8)),
          }),
          scale: interpolate(frame, [0.2 * fps, 0.55 * fps], [1.5, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(1.8)),
            output: "perceptual-scale",
          }),
        }}
      >
        {prLabel}
      </div>
      <div
        style={{
          position: "absolute",
          left: 210,
          top: 390,
          width: 660,
          height: 660,
          borderRadius: 330,
          border: "16px solid #E8C872",
          boxShadow: "inset 0 0 0 10px #8A6840, 0 0 0 8px #8A6840",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#E8C872",
          fontFamily,
          fontSize: 240,
          lineHeight: 1,
          opacity: interpolate(frame, [0, 0.2 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          scale: interpolate(frame, [0, 0.45 * fps], [1.7, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(1.45)),
            output: "perceptual-scale",
          }),
          rotate: interpolate(frame, [0, 0.45 * fps], ["-28deg", "-8deg"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(1.45)),
          }),
        }}
      >
        金
      </div>
      <div
        style={{
          position: "absolute",
          left: 390,
          top: 1110,
          width: interpolate(frame, [0.4 * fps, 0.85 * fps], [0, 300], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          height: 6,
          backgroundColor: "#E8C872",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 130,
          top: 1160,
          width: 820,
          textAlign: "center",
          color: "#F6E7C1",
          fontFamily,
          fontSize: 86,
          fontWeight: 700,
          lineHeight: 1.35,
          whiteSpace: "pre-wrap",
          textWrap: "balance",
          opacity: interpolate(frame, [0.4 * fps, 0.85 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [0.4 * fps, 0.85 * fps], ["0px 28px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        {line}
      </div>
    </AbsoluteFill>
  );
};

export const MoneyStampComposition = () => {
  return (
    <Composition
      id="MoneyStamp"
      component={MoneyStamp}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "固定費、一度並べてみて",
        prLabel: "#PR",
      }}
    />
  );
};
