import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Sawarabi Mincho";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/sawarabi-mincho-400.woff2"),
  weight: "400",
});

const frameLength = 2 * (760 + 1320);

/** 美容: 金の枠線が一周して閉じる。 */
export const BeautyFrame: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#101010", overflow: "hidden", fontFamily, fontWeight: 400 }}>
      <svg width={END_CARD_WIDTH} height={END_CARD_HEIGHT} style={{ position: "absolute", inset: 0 }}>
        <rect
          x={160}
          y={240}
          width={760}
          height={1320}
          fill="none"
          stroke="#D7B57A"
          strokeWidth={6}
          strokeDasharray={frameLength}
          strokeDashoffset={interpolate(frame, [0, 0.85 * fps], [frameLength, 0], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.cubic),
          })}
        />
      </svg>
      <div
        style={{
          position: "absolute",
          left: 220,
          top: 700,
          width: 660,
          textAlign: "center",
          color: "#F4E6CF",
          fontFamily,
          fontSize: 84,
          lineHeight: 1.45,
          whiteSpace: "pre-wrap",
          textWrap: "balance",
          opacity: interpolate(frame, [0.55 * fps, 0.95 * fps], [0, 1], {
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
          left: 220,
          top: 1280,
          width: 660,
          textAlign: "center",
          color: "#D7B57A",
          fontFamily,
          fontSize: 48,
          opacity: interpolate(frame, [0.75 * fps, 1.05 * fps], [0, 1], {
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

export const BeautyFrameComposition = () => {
  return (
    <Composition
      id="BeautyFrame"
      component={BeautyFrame}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "鏡の距離、少し変えてみて",
        prLabel: "#PR",
      }}
    />
  );
};
