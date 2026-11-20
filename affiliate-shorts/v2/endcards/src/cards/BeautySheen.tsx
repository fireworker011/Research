import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Zen Antique";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/zen-antique-400.woff2"),
  weight: "400",
});

/** 美容: 真珠地に光の筋が横切る。 */
export const BeautySheen: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#F6EFEA",
        backgroundImage: "linear-gradient(160deg, #FBF7F4 0%, #E7D5CC 100%)",
        overflow: "hidden",
        fontFamily,
        fontWeight: 400,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 150,
          top: 340,
          width: 780,
          height: 1180,
          borderRadius: "50%",
          border: "3px solid #C48B7A",
          opacity: interpolate(frame, [0.15 * fps, 0.5 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          top: -300,
          width: 160,
          height: 2600,
          background:
            "linear-gradient(90deg, rgba(255,255,255,0) 0%, rgba(255,255,255,0.9) 50%, rgba(255,255,255,0) 100%)",
          rotate: "18deg",
          translate: interpolate(frame, [0, 0.85 * fps], ["-420px 0px", "980px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.linear,
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 170,
          top: 820,
          width: 740,
          textAlign: "center",
          color: "#6D4540",
          fontFamily,
          fontSize: 86,
          lineHeight: 1.45,
          whiteSpace: "pre-wrap",
          textWrap: "balance",
          opacity: interpolate(frame, [0.35 * fps, 0.75 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.4, 0, 0.2, 1),
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
          top: 1320,
          textAlign: "center",
          color: "#C48B7A",
          fontFamily,
          fontSize: 48,
          opacity: interpolate(frame, [0.55 * fps, 0.9 * fps], [0, 1], {
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

export const BeautySheenComposition = () => {
  return (
    <Composition
      id="BeautySheen"
      component={BeautySheen}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "いつもの順番、一度見て",
        prLabel: "#PR",
      }}
    />
  );
};
