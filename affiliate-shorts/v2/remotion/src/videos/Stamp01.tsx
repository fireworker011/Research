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
import { loadFont } from "@remotion/google-fonts/NotoSansJP";
import { cues } from "../cues";
import { activeCue, cueIndex } from "../time";

const { fontFamily, waitUntilDone } = loadFont("normal", {
  weights: ["700", "900"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});
const fontHandle = delayRender("noto-sans-jp");
waitUntilDone().then(() => {
  continueRender(fontHandle);
});

const list = cues["01"];

export const Stamp01: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const cue = activeCue(list, t);
  const index = cueIndex(list, t);
  const pr = t >= 20;

  const slipY = interpolate(frame, [0, 20 * fps], [40, -30], {
    extrapolateRight: "clamp",
  });
  const calcRot = interpolate(frame, [0, 20 * fps], [-8, 4]);
  const workerScale = interpolate(frame, [0, 20 * fps], [1, 1.06]);

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 18% 0%, #F8EFD6 0%, #E7D3A8 62%, #CDB98A 100%)",
        fontFamily,
        color: "#2C2416",
        overflow: "hidden",
      }}
    >
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(0deg, rgba(90,60,20,0.04) 0 1px, transparent 1px 7px)",
        }}
      />
      {pr ? (
        <PrCard fontFamily={fontFamily} lines={cue.lines} />
      ) : (
        <>
          <div
            style={{
              position: "absolute",
              top: 120,
              right: 80,
              width: 168,
              height: 168,
              borderRadius: "50%",
              border: "8px solid #B4332A",
              color: "#B4332A",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontWeight: 900,
              fontSize: 52,
              transform: "rotate(8deg)",
              background: "rgba(255,248,236,0.72)",
            }}
          >
            明細
          </div>
          <div
            style={{
              position: "absolute",
              top: 190 + slipY,
              left: 70,
              width: 520,
              height: 150,
              overflow: "hidden",
              transform: "rotate(-7deg)",
              opacity: index >= 3 ? 1 : 0.35,
              filter: "drop-shadow(0 18px 24px rgba(60,30,10,0.18))",
            }}
          >
            <Img
              src={staticFile("ira/payslip.png")}
              style={{ width: 520, height: "auto", display: "block" }}
            />
          </div>
          <Img
            src={staticFile("ira/calc.png")}
            style={{
              position: "absolute",
              left: 36,
              top: 980,
              width: 220,
              transform: `rotate(${calcRot}deg)`,
              opacity: index >= 5 ? 1 : 0.2,
            }}
          />
          <Img
            src={staticFile("ira/worker.png")}
            style={{
              position: "absolute",
              right: 20,
              top: 900,
              width: 300,
              transform: `scale(${workerScale})`,
              transformOrigin: "50% 0%",
              opacity: index >= 7 ? 1 : 0.15,
            }}
          />
          <div
            style={{
              position: "absolute",
              left: 80,
              right: 80,
              top: 430,
              textAlign: "center",
              fontWeight: 900,
              fontSize: 168,
              letterSpacing: -2,
              color: "#B4332A",
              lineHeight: 1,
              textShadow: "0 8px 0 rgba(255,248,236,0.8)",
            }}
          >
            5/1000
          </div>
          <div
            style={{
              position: "absolute",
              left: 90,
              right: 90,
              bottom: 160,
              display: "flex",
              justifyContent: "center",
            }}
          >
            <div
              style={{
                border: "6px solid #B4332A",
                background: "rgba(255,248,236,0.94)",
                padding: "22px 36px",
                fontWeight: 700,
                fontSize: 52,
                lineHeight: 1.25,
                textAlign: "center",
                zIndex: 3,
              }}
            >
              {cue.lines.map((line) => (
                <div key={line}>{line}</div>
              ))}
            </div>
          </div>
        </>
      )}
    </AbsoluteFill>
  );
};

const PrCard: React.FC<{ fontFamily: string; lines: string[] }> = ({
  fontFamily,
  lines,
}) => {
  return (
    <AbsoluteFill
      style={{
        fontFamily,
        background: "#F6E7C8",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div style={{ fontWeight: 900, fontSize: 120, color: "#B4332A" }}>
        {lines[0]}
      </div>
      <div style={{ marginTop: 24, fontWeight: 700, fontSize: 56 }}>
        {lines[1]}
      </div>
      <div
        style={{
          position: "absolute",
          bottom: 120,
          fontSize: 32,
          lineHeight: 1.6,
          textAlign: "center",
          color: "#5C4A32",
        }}
      >
        <div>イラスト：いらすとや</div>
        <div>VOICEVOX:冥鳴ひまり</div>
      </div>
    </AbsoluteFill>
  );
};
