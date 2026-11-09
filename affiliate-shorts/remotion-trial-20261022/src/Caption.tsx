import { Easing, interpolate, useCurrentFrame, useVideoConfig } from "remotion";
import { FONT } from "./font";
import { LINES } from "./lines";

export const Caption = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const time = frame / fps;
  const line = LINES.find((item) => time >= item.start && time < item.end);
  if (!line) {
    return null;
  }
  const local = time - line.start;
  const enter = interpolate(local, [0, 0.12], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.cubic),
  });

  return (
    <div
      style={{
        position: "absolute",
        left: 64,
        right: 64,
        bottom: 108,
        zIndex: 5,
        opacity: enter,
        translate: `0px ${(1 - enter) * 18}px`,
      }}
    >
      <div
        style={{
          backgroundColor: "rgba(12,10,8,0.92)",
          color: "#FFF8EC",
          fontFamily: FONT,
          fontSize: 46,
          lineHeight: 1.35,
          textAlign: "center",
          padding: "22px 28px",
          borderRadius: 20,
        }}
      >
        {line.text}
      </div>
    </div>
  );
};
