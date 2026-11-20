import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Mochiy Pop One";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/mochiy-pop-one-400.woff2"),
  weight: "400",
});

/** ペット: 丸いカードが弾んで着地する。 */
export const PetBounce: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#D5E7A4", overflow: "hidden", fontFamily, fontWeight: 400 }}>
      <div
        style={{
          position: "absolute",
          left: -120,
          top: -160,
          width: 640,
          height: 640,
          borderRadius: 320,
          backgroundColor: "#F7FBE8",
        }}
      />
      <div
        style={{
          position: "absolute",
          right: -40,
          top: 220,
          width: 120,
          height: 120,
          borderRadius: 60,
          backgroundColor: "#F28B4A",
          translate: interpolate(frame, [0, 0.8 * fps], ["0px -520px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bounce,
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 1320,
          width: 70,
          height: 70,
          borderRadius: 35,
          backgroundColor: "#3E6B2E",
          translate: interpolate(frame, [0.15 * fps, 0.95 * fps], ["0px -700px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bounce,
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 120,
          top: 460,
          width: 840,
          minHeight: 860,
          borderRadius: 72,
          backgroundColor: "#FFFDF6",
          boxShadow: "0 28px 0 #3E6B2E",
          padding: "80px 64px",
          translate: interpolate(frame, [0, 0.7 * fps], ["0px -900px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bounce,
          }),
          rotate: interpolate(frame, [0, 0.7 * fps], ["-8deg", "0deg"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bounce,
          }),
        }}
      >
        <div
          style={{
            alignSelf: "flex-start",
            display: "inline-block",
            backgroundColor: "#3E6B2E",
            color: "#F4FFE6",
            fontFamily,
            fontSize: 48,
            padding: "8px 22px",
            borderRadius: 18,
          }}
        >
          {prLabel}
        </div>
        <div
          style={{
            marginTop: 48,
            width: 700,
            color: "#234018",
            fontFamily,
            fontSize: 84,
            lineHeight: 1.4,
            whiteSpace: "pre-wrap",
            textWrap: "balance",
          }}
        >
          {line}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const PetBounceComposition = () => {
  return (
    <Composition
      id="PetBounce"
      component={PetBounce}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "帰ってから、今日の様子を見て",
        prLabel: "#PR",
      }}
    />
  );
};
