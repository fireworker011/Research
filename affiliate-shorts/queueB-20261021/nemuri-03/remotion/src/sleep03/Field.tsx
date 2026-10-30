import type { ReactNode } from "react";
import { AbsoluteFill, useCurrentFrame } from "remotion";
import { BG } from "./theme";

// Bottom third (y >= 1280) stays empty. Subtitles are added in a later phase.
export const Field = ({ children }: { children: ReactNode }) => {
  const frame = useCurrentFrame();
  const zoom = 1 + Math.max(0, frame) * 0.00015;
  const gx = 48 + Math.sin(frame / 36) * 9;
  const gy = 38 + Math.cos(frame / 44) * 7;

  return (
    <AbsoluteFill style={{ backgroundColor: BG, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(circle at ${gx}% ${gy}%, #1C4030 0%, ${BG} 62%)`,
          transform: `scale(${zoom})`,
        }}
      />
      <AbsoluteFill style={{ transform: `scale(${zoom})` }}>{children}</AbsoluteFill>
    </AbsoluteFill>
  );
};
