import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Zen Maru Gothic";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/zen-maru-gothic-900.woff2"),
  weight: "900",
});

const rings = [
  { id: "ring-a", delay: 0 },
  { id: "ring-b", delay: 0.22 },
  { id: "ring-c", delay: 0.44 },
] as const;

/** ペット: 肉球の周りに心拍の輪が広がる。 */
export const PetPulse: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#F8E6D4", overflow: "hidden", fontFamily, fontWeight: 900 }}>
      {rings.map((ring) => (
        <div
          key={ring.id}
          style={{
            position: "absolute",
            left: 250,
            top: 300,
            width: 580,
            height: 580,
            borderRadius: 290,
            border: "10px solid #E07A45",
            opacity: interpolate(frame, [ring.delay * fps, (ring.delay + 0.9) * fps], [0.75, 0], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
            scale: interpolate(frame, [ring.delay * fps, (ring.delay + 0.9) * fps], [0.45, 1.7], {
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
          left: 390,
          top: 470,
          width: 300,
          height: 250,
          scale: interpolate(frame, [0, 0.35 * fps], [0.4, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            output: "perceptual-scale",
          }),
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 70,
            top: 90,
            width: 160,
            height: 140,
            borderRadius: 80,
            backgroundColor: "#6B3A2A",
          }}
        />
        {[
          { id: "toe-1", left: 18, top: 62 },
          { id: "toe-2", left: 78, top: 8 },
          { id: "toe-3", left: 150, top: 8 },
          { id: "toe-4", left: 210, top: 62 },
        ].map((toe) => (
          <div
            key={toe.id}
            style={{
              position: "absolute",
              left: toe.left,
              top: toe.top,
              width: 72,
              height: 86,
              borderRadius: 40,
              backgroundColor: "#6B3A2A",
            }}
          />
        ))}
      </div>
      <div
        style={{
          position: "absolute",
          left: 130,
          top: 1040,
          width: 820,
          textAlign: "center",
          color: "#4A2418",
          fontFamily,
          fontWeight: 900,
          fontSize: 84,
          lineHeight: 1.35,
          whiteSpace: "pre-wrap",
          textWrap: "balance",
          opacity: interpolate(frame, [0.25 * fps, 0.6 * fps], [0, 1], {
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
          left: 130,
          top: 1560,
          padding: "10px 28px",
          borderRadius: 999,
          backgroundColor: "#E07A45",
          color: "#FFF8F2",
          fontFamily,
          fontWeight: 900,
          fontSize: 48,
          scale: interpolate(frame, [0.45 * fps, 0.75 * fps], [0.2, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            output: "perceptual-scale",
          }),
        }}
      >
        {prLabel}
      </div>
    </AbsoluteFill>
  );
};

export const PetPulseComposition = () => {
  return (
    <Composition
      id="PetPulse"
      component={PetPulse}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "うちの子の留守中も見てみて",
        prLabel: "#PR",
      }}
    />
  );
};
