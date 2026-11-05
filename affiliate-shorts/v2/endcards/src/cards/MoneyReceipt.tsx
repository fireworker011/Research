import { loadFont } from "@remotion/fonts";
import { AbsoluteFill, Composition, Easing, interpolate, staticFile, useCurrentFrame, useVideoConfig } from "remotion";
import { END_CARD_DURATION, END_CARD_FPS, END_CARD_HEIGHT, END_CARD_WIDTH, endCardSchema, type EndCardProps } from "../end-card";

const fontFamily = "IBM Plex Sans JP";

void loadFont({
  family: fontFamily,
  url: staticFile("fonts/ibm-plex-sans-jp-700.woff2"),
  weight: "700",
});

/** 金メモ: 紙のメモが下からせり上がる。 */
export const MoneyReceipt: React.FC<EndCardProps> = ({ line, prLabel }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ backgroundColor: "#16332C", overflow: "hidden", fontFamily, fontWeight: 700 }}>
      <div
        style={{
          position: "absolute",
          left: 90,
          top: 250,
          width: 900,
          height: 1320,
          backgroundColor: "#F3EEE4",
          borderRadius: 8,
          boxShadow: "0 40px 90px rgba(0,0,0,0.35)",
          translate: interpolate(frame, [0, 0.7 * fps], ["0px 1100px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.out(Easing.cubic),
          }),
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            padding: "22px 28px 0",
          }}
        >
          {["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"].map((id) => (
            <div
              key={id}
              style={{
                width: 26,
                height: 26,
                borderRadius: 13,
                backgroundColor: "#16332C",
              }}
            />
          ))}
        </div>
        <div
          style={{
            marginTop: 48,
            marginLeft: 72,
            color: "#147A63",
            fontFamily,
            fontWeight: 700,
            fontSize: 48,
            opacity: interpolate(frame, [0.45 * fps, 0.7 * fps], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {prLabel}
        </div>
        <div
          style={{
            marginTop: 20,
            marginLeft: 72,
            width: interpolate(frame, [0.4 * fps, 0.85 * fps], [0, 220], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
              easing: Easing.out(Easing.cubic),
            }),
            height: 8,
            backgroundColor: "#147A63",
          }}
        />
        <div
          style={{
            marginTop: 36,
            marginLeft: 72,
            width: 740,
            color: "#1A2E28",
            fontFamily,
            fontWeight: 700,
            fontSize: 84,
            lineHeight: 1.35,
            textAlign: "left",
            whiteSpace: "pre-wrap",
            opacity: interpolate(frame, [0.5 * fps, 0.9 * fps], [0, 1], {
              extrapolateLeft: "clamp",
              extrapolateRight: "clamp",
            }),
          }}
        >
          {line}
        </div>
        <div style={{ marginTop: 48, marginLeft: 72, marginRight: 72 }}>
          {["row-1", "row-2", "row-3", "row-4"].map((id, index) => (
            <div
              key={id}
              style={{
                marginTop: 36,
                height: 0,
                borderTop: "4px dashed #C9C0B0",
                opacity: interpolate(frame, [(0.7 + index * 0.12) * fps, (0.9 + index * 0.12) * fps], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
              }}
            />
          ))}
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const MoneyReceiptComposition = () => {
  return (
    <Composition
      id="MoneyReceipt"
      component={MoneyReceipt}
      durationInFrames={END_CARD_DURATION}
      fps={END_CARD_FPS}
      width={END_CARD_WIDTH}
      height={END_CARD_HEIGHT}
      schema={endCardSchema}
      defaultProps={{
        line: "先に引かれる分だけ見て",
        prLabel: "#PR",
      }}
    />
  );
};
