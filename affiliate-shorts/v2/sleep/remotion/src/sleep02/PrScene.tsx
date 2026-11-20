import { AbsoluteFill, Easing, interpolate, useCurrentFrame } from "remotion";
import { sansFamily } from "../sans";

export const PrScene = () => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#E23D12", overflow: "hidden" }}>
      <div
        style={{
          position: "absolute",
          left: 72,
          right: 72,
          top: 220,
          bottom: 140,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "flex-start",
          gap: 8,
          opacity: interpolate(frame, [0, 4], [0, 1], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
          }),
          translate: interpolate(frame, [0, 5], ["0px 24px", "0px 0px"], {
            extrapolateLeft: "clamp",
            extrapolateRight: "clamp",
            easing: Easing.bezier(0.16, 1, 0.3, 1),
          }),
        }}
      >
        <div
          style={{
            fontFamily: sansFamily,
            fontWeight: 900,
            fontSize: 44,
            color: "#F6E6D2",
          }}
        >
          ねむりの棚
        </div>
        <div
          style={{
            fontFamily: sansFamily,
            fontWeight: 900,
            fontSize: 92,
            color: "#FFF8F2",
            lineHeight: 1.15,
          }}
        >
          詳しくは
        </div>
        <div
          style={{
            fontFamily: sansFamily,
            fontWeight: 900,
            fontSize: 84,
            color: "#FFF8F2",
            lineHeight: 1.15,
          }}
        >
          プロフィールの
        </div>
        <div
          style={{
            fontFamily: sansFamily,
            fontWeight: 900,
            fontSize: 84,
            color: "#1A120C",
            lineHeight: 1.15,
          }}
        >
          リンク（PR）
        </div>
      </div>
    </AbsoluteFill>
  );
};
