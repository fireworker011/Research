import type { ReactNode } from "react";
import { AbsoluteFill } from "remotion";

const PAPER = "#F7F1E6";
const INK = "#1A1612";

export const Stage = ({ children }: { children: ReactNode }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: PAPER, color: INK, overflow: "hidden" }}>
      {children}
    </AbsoluteFill>
  );
};

export const INK_COLOR = INK;
export const YELLOW = "#F0B429";
export const INK_CARD = "#1A1612";
