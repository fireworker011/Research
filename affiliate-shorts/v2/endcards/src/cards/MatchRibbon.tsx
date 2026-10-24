import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "Zen Old Mincho";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/zen-old-mincho-700.woff2"),
  weight: "700",
});

const gems = [
  { id: "gem-1", left: 140, top: 420, delay: 0.45 },
  { id: "gem-2", left: 860, top: 1280, delay: 0.6 },
  { id: "gem-3", left: 180, top: 1460, delay: 0.75 },
] as const;

/** 婚活: 斜めのリボンが横に伸びる。 */
export const MatchRibbon: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#3A1020", overflow: "hidden", fontFamily, fontWeight: 700 }}>
      <div
        style={{
          position: "absolute",
          left: 80,
          top: 360,
          color: "#F3D5A0",
          fontFamily,
          fontSize: 56,
          letterSpacing: 6,
          opacity: interpolate(frame, [0, 0.3 * fps], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          translate: interpolate(frame, [0, 0.4 * fps], ["-40px 0px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.quad),
          }),
        }}
      >
        {prLabel}
      </div>
      <div
        style={{
          position: "absolute",
          left: -160,
          top: 660,
          height: 560,
          backgroundColor: "#F3D5A0",
          rotate: "-8deg",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          overflow: "hidden",
          width: interpolate(frame, [0.1 * fps, 0.6 * fps], [0, 1480], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.quad),
          }),
        }}
      >
        <div
          style={{
            width: 680,
            textAlign: "center",
            color: "#3A1020",
            fontFamily,
            fontSize: 84,
            lineHeight: 1.35,
            whiteSpace: "pre-wrap",
            textWrap: "balance",
            opacity: interpolate(frame, [0.4 * fps, 0.7 * fps], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {line}
        </div>
      </div>
      {gems.map((gem) => (
        <div
          key={gem.id}
          style={{
            position: "absolute",
            left: gem.left,
            top: gem.top,
            width: 28,
            height: 28,
            backgroundColor: "#F3D5A0",
            rotate: "45deg",
            scale: interpolate(frame, [gem.delay * fps, (gem.delay + 0.25) * fps], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              output: "perceptual-scale",
            }),
          }}
        />
      ))}
    </AbsoluteFill>
  );
};

export const MatchRibbonComposition = () => {
  return (
    <Composition
      id="MatchRibbon"
      component={MatchRibbon}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "写真の1枚目を見てみて",
        prLabel: "#PR",
      }}
    />
  );
};
