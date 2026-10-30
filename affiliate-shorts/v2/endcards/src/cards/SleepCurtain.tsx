import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "BIZ UDPGothic";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/biz-udpgothic-700.woff2"),
  weight: "700",
});

/** 睡眠: カーテンが左右に開く。 */
export const SleepCurtain: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#F3E6D4", overflow: "hidden", fontFamily, fontWeight: 700 }}>
      <div
        style={{
          position: "absolute",
          left: 140,
          top: 720,
          width: 800,
          textAlign: "center",
          color: "#2C2622",
          fontFamily,
          fontSize: 84,
          fontWeight: 700,
          lineHeight: 1.4,
          whiteSpace: "pre-wrap",
          textWrap: "balance",
        }}
      >
        {line}
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 1120,
          textAlign: "center",
          color: "#8A7564",
          fontFamily,
          fontSize: 52,
          fontWeight: 700,
        }}
      >
        {prLabel}
      </div>
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 0,
          width: 560,
          height: "100%",
          backgroundColor: "#2C2622",
          boxShadow: "inset -18px 0 0 #8A7564",
          translate: interpolate(frame, [0, 0.85 * fps], ["0px 0px", "-560px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.cubic),
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 0,
          top: 0,
          width: 560,
          height: "100%",
          backgroundColor: "#2C2622",
          boxShadow: "inset 18px 0 0 #8A7564",
          translate: interpolate(frame, [0, 0.85 * fps], ["0px 0px", "560px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.cubic),
          }),
        }}
      />
    </AbsoluteFill>
  );
};

export const SleepCurtainComposition = () => {
  return (
    <Composition
      id="SleepCurtain"
      component={SleepCurtain}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "寝る前の画面、一度閉じて",
        prLabel: "#PR",
      }}
    />
  );
};
