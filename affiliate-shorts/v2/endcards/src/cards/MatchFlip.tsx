import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Kaisei Decol";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/kaisei-decol-700.woff2"),
  weight: "700",
});

/** 婚活: プロフィールカードが横から開く。 */
export const MatchFlip: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#F6D5DE", overflow: "hidden", fontFamily, fontWeight: 700 }}>
      <div
        style={{
          position: "absolute",
          left: 150,
          top: 300,
          width: 780,
          height: 1240,
          borderRadius: 36,
          backgroundColor: "#FFF9F7",
          boxShadow: "0 30px 70px rgba(122, 48, 72, 0.18)",
          transformOrigin: "center center",
          scale: interpolate(frame, [0, 0.55 * fps], ["0.06 1", "1 1"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          }),
          opacity: interpolate(frame, [0, 0.12 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      >
        <div
          style={{
            margin: "72px auto 0",
            width: 180,
            height: 180,
            borderRadius: 90,
            border: "10px solid #E7B7C4",
            backgroundColor: "#F8E4EA",
          }}
        />
        <div
          style={{
            margin: "18px auto 0",
            width: 240,
            height: 28,
            borderRadius: 14,
            backgroundColor: "#F0D0D8",
          }}
        />
        <div
          style={{
            marginTop: 80,
            padding: "0 72px",
            textAlign: "center",
            color: "#7A3048",
            fontFamily,
            fontSize: 88,
            lineHeight: 1.35,
            whiteSpace: "pre-wrap",
            textWrap: "balance",
            opacity: interpolate(frame, [0.4 * fps, 0.75 * fps], [0, 1], {
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
            left: 0,
            right: 0,
            bottom: 64,
            textAlign: "center",
            color: "#C4798E",
            fontFamily,
            fontSize: 48,
          }}
        >
          {prLabel}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const MatchFlipComposition = () => {
  return (
    <Composition
      id="MatchFlip"
      component={MatchFlip}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "プロフィールを見直そう",
        prLabel: "#PR",
      }}
    />
  );
};
