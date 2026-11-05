import React from "react";
import {
  AbsoluteFill,
  Img,
  continueRender,
  delayRender,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/NotoSerifJP";
import { cues } from "../cues";
import { activeCue } from "../time";

const { fontFamily, waitUntilDone } = loadFont("normal", {
  weights: ["600", "900"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});
const fontHandle = delayRender("noto-serif-jp");
waitUntilDone().then(() => {
  continueRender(fontHandle);
});

const list = cues["02"];

export const Split02: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const t = frame / fps;
  const cue = activeCue(list, t);
  const pr = t >= 46;
  const bookScale = interpolate(frame, [0, durationInFrames], [1, 1.08]);
  const officeY = interpolate(frame, [0, durationInFrames], [40, -50]);

  if (pr) {
    return (
      <AbsoluteFill
        style={{
          fontFamily,
          background: "#0E1A33",
          color: "#E4C36A",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <div style={{ fontWeight: 900, fontSize: 120 }}>{cue.lines[0]}</div>
        <div style={{ marginTop: 28, fontWeight: 600, fontSize: 56, color: "#F7F1DE" }}>
          {cue.lines[1]}
        </div>
        <div
          style={{
            position: "absolute",
            bottom: 120,
            fontSize: 32,
            lineHeight: 1.6,
            textAlign: "center",
            color: "#C8B48A",
          }}
        >
          <div>イラスト：いらすとや</div>
          <div>VOICEVOX:冥鳴ひまり</div>
        </div>
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill style={{ fontFamily, overflow: "hidden", background: "#0E1A33" }}>
      <div style={{ position: "absolute", left: 0, top: 0, width: 540, height: 1920, background: "#E4C36A" }} />
      <div style={{ position: "absolute", left: 540, top: 0, width: 540, height: 1920, background: "#0E1A33" }} />
      <div style={{ position: "absolute", left: 532, top: 0, width: 16, height: 1920, background: "#F7F1DE" }} />
      <div
        style={{
          position: "absolute",
          left: 48,
          top: 120,
          writingMode: "vertical-rl",
          fontWeight: 900,
          fontSize: 64,
          letterSpacing: 8,
          color: "#0E1A33",
        }}
      >
        会社
      </div>
      <div
        style={{
          position: "absolute",
          right: 48,
          top: 120,
          writingMode: "vertical-rl",
          fontWeight: 900,
          fontSize: 64,
          letterSpacing: 8,
          color: "#E4C36A",
        }}
      >
        本人
      </div>
      <Img
        src={staticFile("ira/nenkin.png")}
        style={{
          position: "absolute",
          left: 80,
          top: 280,
          width: 360,
          transform: `scale(${bookScale})`,
          transformOrigin: "50% 50%",
        }}
      />
      <Img
        src={staticFile("ira/office.png")}
        style={{
          position: "absolute",
          left: 620,
          top: 300 + officeY,
          width: 380,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 140,
          right: 140,
          top: 860,
          textAlign: "center",
          fontWeight: 900,
          fontSize: 72,
          color: t < 7 ? "#0E1A33" : "#F7F1DE",
          background: t < 7 ? "#E4C36A" : "#0E1A33",
          padding: "16px 12px",
          border: "4px solid #E4C36A",
        }}
      >
        {t < 7 ? "？" : "18.300%"}
      </div>
      <div
        style={{
          position: "absolute",
          left: 390,
          top: 1060,
          height: 720,
          writingMode: "vertical-rl",
          fontWeight: 600,
          fontSize: 52,
          lineHeight: 1.45,
          color: "#0E1A33",
          background: "#F7F1DE",
          padding: "28px 18px",
        }}
      >
        {cue.lines.map((line) => (
          <div key={line}>{line}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
