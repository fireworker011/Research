import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Kosugi Maru";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/kosugi-maru-400.woff2"),
  weight: "400",
});

/** 婚活: 円いスポットが広がって文字を出す。 */
export const MatchSpot: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#5C3144", overflow: "hidden", fontFamily, fontWeight: 400 }}>
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 360,
          width: 840,
          height: 840,
          borderRadius: 450,
          backgroundColor: "#F8E7EE",
          scale: interpolate(frame, [0, 0.6 * fps], [0.08, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(1.35)),
            output: "perceptual-scale",
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 180,
          top: 620,
          width: 760,
          textAlign: "center",
          color: "#5C2438",
          fontFamily,
          fontSize: 86,
          lineHeight: 1.4,
          whiteSpace: "pre-wrap",
          textWrap: "balance",
          opacity: interpolate(frame, [0.35 * fps, 0.7 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          scale: interpolate(frame, [0.35 * fps, 0.7 * fps], [0.86, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.back(1.2)),
            output: "perceptual-scale",
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
          top: 1560,
          textAlign: "center",
          color: "#F8E7EE",
          fontFamily,
          fontSize: 52,
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

export const MatchSpotComposition = () => {
  return (
    <Composition
      id="MatchSpot"
      component={MatchSpot}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "自己紹介を短くしてみて",
        prLabel: "#PR",
      }}
    />
  );
};
