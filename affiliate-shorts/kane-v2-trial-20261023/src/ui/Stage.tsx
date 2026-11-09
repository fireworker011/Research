import { AbsoluteFill, useCurrentFrame } from "remotion";
import { CREAM } from "../theme";

export const Stage: React.FC<{
  readonly tint: string;
  readonly children: React.ReactNode;
}> = ({ tint, children }) => {
  const frame = useCurrentFrame();
  const drift = Math.sin(frame / 24) * 10;

  return (
    <AbsoluteFill style={{ backgroundColor: CREAM }}>
      <div
        style={{
          position: "absolute",
          left: 150,
          top: 120 + drift,
          width: 780,
          height: 780,
          borderRadius: 390,
          backgroundColor: tint,
        }}
      />
      {children}
    </AbsoluteFill>
  );
};
