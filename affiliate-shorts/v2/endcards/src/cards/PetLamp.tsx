import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Klee One";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/klee-one-600.woff2"),
  weight: "600",
});

/** ペット: 夜の部屋にランプの光が広がる。 */
export const PetLamp: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#12182A", overflow: "hidden", fontFamily, fontWeight: 600 }}>
      <div
        style={{
          position: "absolute",
          left: 90,
          top: 80,
          width: 900,
          height: 900,
          borderRadius: 450,
          background:
            "radial-gradient(circle, rgba(246,194,122,0.95) 0%, rgba(246,194,122,0.28) 46%, rgba(246,194,122,0) 70%)",
          opacity: interpolate(frame, [0, 0.8 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.22, 1, 0.36, 1),
          }),
          scale: interpolate(frame, [0, 0.9 * fps], [0.35, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.22, 1, 0.36, 1),
            output: "perceptual-scale",
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 340,
          top: 980,
          width: 400,
          height: 70,
          borderRadius: "50%",
          backgroundColor: "rgba(0,0,0,0.45)",
          scale: interpolate(frame, [0.2 * fps, 0.8 * fps], [0.2, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            output: "perceptual-scale",
          }),
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 100,
          top: 150,
          color: "#F6C27A",
          fontFamily,
          fontSize: 52,
          border: "3px solid #F6C27A",
          padding: "8px 22px",
          opacity: interpolate(frame, [0.15 * fps, 0.45 * fps], [0, 1], {
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
          left: 100,
          top: 1180,
          width: 820,
          textAlign: "left",
          color: "#F6E7D0",
          fontFamily,
          fontSize: 84,
          lineHeight: 1.4,
          whiteSpace: "pre-wrap",
          opacity: interpolate(frame, [0.35 * fps, 0.9 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
          translate: interpolate(frame, [0.35 * fps, 0.9 * fps], ["0px 40px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        {line}
      </div>
      <div
        style={{
          position: "absolute",
          left: 100,
          top: 1560,
          width: 22,
          height: 22,
          borderRadius: 11,
          backgroundColor: "#F6C27A",
          opacity: interpolate(frame, [0, 8, 16, 24, 32, 40, 48, 56], [0.25, 1, 0.3, 1, 0.35, 1, 0.3, 0.9], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
        }}
      />
    </AbsoluteFill>
  );
};

export const PetLampComposition = () => {
  return (
    <Composition
      id="PetLamp"
      component={PetLamp}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "留守のあいだ、様子を見て",
        prLabel: "#PR",
      }}
    />
  );
};
