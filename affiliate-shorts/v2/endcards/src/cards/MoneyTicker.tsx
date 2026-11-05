import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Dela Gothic One";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/dela-gothic-one-400.woff2"),
  weight: "400",
});

/** 金メモ: 電光ボードが左右から閉じる。 */
export const MoneyTicker: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#07111A", overflow: "hidden", fontFamily, fontWeight: 400 }}>
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(180deg, rgba(214,255,74,0.05) 0px, rgba(214,255,74,0.05) 2px, transparent 2px, transparent 10px)",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 70,
          top: 70,
          width: 70,
          height: 70,
          borderTop: "8px solid #D6FF4A",
          borderLeft: "8px solid #D6FF4A",
        }}
      />
      <div
        style={{
          position: "absolute",
          right: 70,
          bottom: 220,
          width: 70,
          height: 70,
          borderBottom: "8px solid #D6FF4A",
          borderRight: "8px solid #D6FF4A",
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 0,
          top: 690,
          height: 520,
          backgroundColor: "#D6FF4A",
          width: interpolate(frame, [0, 0.45 * fps], [0, 1080], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.inOut(Easing.exp),
          }),
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
        }}
      >
        <div
          style={{
            width: 860,
            color: "#102000",
            fontFamily,
            fontSize: 84,
            lineHeight: 1.3,
            textAlign: "center",
            whiteSpace: "pre-wrap",
            textWrap: "balance",
            opacity: interpolate(frame, [0.3 * fps, 0.55 * fps], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {line}
        </div>
      </div>
      <div
        style={{
          position: "absolute",
          top: 540,
          right: 72,
          padding: "14px 28px",
          backgroundColor: "#7C5CFF",
          color: "#F4F1FF",
          fontFamily,
          fontSize: 48,
          lineHeight: 1,
          translate: interpolate(frame, [0.1 * fps, 0.5 * fps], ["280px 0px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.exp),
          }),
        }}
      >
        {prLabel}
      </div>
    </AbsoluteFill>
  );
};

export const MoneyTickerComposition = () => {
  return (
    <Composition
      id="MoneyTicker"
      component={MoneyTicker}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "今月の残りをメモして",
        prLabel: "#PR",
      }}
    />
  );
};
