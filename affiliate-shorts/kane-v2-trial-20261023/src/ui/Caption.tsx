import { interpolate, useCurrentFrame } from "remotion";
import { CAPTION_FONT } from "../font";

export const Caption: React.FC<{ readonly text: string }> = ({ text }) => {
  const frame = useCurrentFrame();
  const enter = interpolate(frame, [0, 4], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 64,
        right: 64,
        bottom: 128,
        zIndex: 5,
        opacity: enter,
        transform: `translateY(${(1 - enter) * 16}px)`,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(28,18,12,0.92)",
          color: "#FFF8EC",
          fontFamily: CAPTION_FONT,
          fontSize: 44,
          fontWeight: 700,
          lineHeight: 1.35,
          textAlign: "center",
          padding: "18px 26px",
          borderRadius: 18,
        }}
      >
        {text}
      </div>
    </div>
  );
};
