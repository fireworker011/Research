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
import { loadFont } from "@remotion/google-fonts/MPLUSRounded1c";
import { cues } from "../cues";
import { activeCue } from "../time";

const { fontFamily, waitUntilDone } = loadFont("normal", {
  weights: ["700", "800"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});
const fontHandle = delayRender("mplus-rounded");
waitUntilDone().then(() => {
  continueRender(fontHandle);
});

const list = cues["03"];

export const Ticket03: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cue = activeCue(list, t);
  const pr = t >= 32;
  const ticketY = interpolate(frame, [0, 32 * fps], [80, -80], {
    extrapolateRight: "clamp",
  });
  const trainX = interpolate(frame, [0, 32 * fps], [40, 280], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        background: "#E7F6F1",
        fontFamily,
        color: "#17211F",
        overflow: "hidden",
      }}
    >
      {pr ? (
        <AbsoluteFill style={{ alignItems: "center", justifyContent: "center" }}>
          <div style={{ fontWeight: 800, fontSize: 120 }}>{cue.lines[0]}</div>
          <div style={{ marginTop: 28, fontWeight: 700, fontSize: 56 }}>{cue.lines[1]}</div>
          <div
            style={{
              position: "absolute",
              bottom: 120,
              fontSize: 32,
              lineHeight: 1.6,
              textAlign: "center",
            }}
          >
            <div>イラスト：いらすとや</div>
            <div>VOICEVOX:冥鳴ひまり</div>
          </div>
        </AbsoluteFill>
      ) : (
        <>
          <Img
            src={staticFile("ira/train.png")}
            style={{
              position: "absolute",
              left: trainX,
              top: 90,
              width: 500,
            }}
          />
          <Img
            src={staticFile("ira/teiki.png")}
            style={{
              position: "absolute",
              left: -20,
              top: 700 + ticketY,
              width: 520,
              transform: "rotate(7deg)",
              filter: "drop-shadow(0 24px 28px rgba(20,40,30,0.16))",
            }}
          />
          <div
            style={{
              position: "absolute",
              right: 64,
              top: 640,
              width: 460,
              fontWeight: 800,
              fontSize: 84,
              lineHeight: 1.2,
            }}
          >
            月15万円
          </div>
          <div
            style={{
              position: "absolute",
              right: 64,
              top: 860,
              width: 460,
              fontWeight: 700,
              fontSize: 48,
              lineHeight: 1.4,
              textAlign: "left",
            }}
          >
            {cue.lines.map((line) => (
              <div key={line}>{line}</div>
            ))}
          </div>
        </>
      )}
    </AbsoluteFill>
  );
};
