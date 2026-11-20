import React from "react";
import {
  AbsoluteFill,
  Easing,
  Img,
  continueRender,
  delayRender,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/MochiyPopOne";

const { fontFamily, waitUntilDone } = loadFont("normal", {
  weights: ["400"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});
const fontHandle = delayRender("mochi-pop-one-fold07");
waitUntilDone().then(() => {
  continueRender(fontHandle);
});

const YELLOW = "#F6E27A";
const INK = "#242424";
const RIM = "#E4CC5C";

/** Body cues only. The last SRT cue is the end card and is not burned in. */
const CUES: { start: number; end: number; lines: string[] }[] = [
  { start: 0, end: 4, lines: ["この0.36は", "給料から引かない。"] },
  { start: 4, end: 12, lines: ["子ども・子育て拠出金。"] },
  { start: 12, end: 18, lines: ["令和八年四月から", "0.36パーセント。"] },
  { start: 18, end: 28, lines: ["事業主が全額負担。", "給与の天引きではない。"] },
];

const CREASE = 1000;
const BAND = 124;
const SHEET_L = 64;
const SHEET_W = 952;
const TOP_FULL = 610;
const BOT_FULL = 650;

const ease = Easing.out(Easing.cubic);

const clamp = (frame: number, from: number, to: number) =>
  interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: ease,
  });

/**
 * Horizontal fold. The rate sits on the yellow leaf, 事業主 on the ink leaf.
 * Captions sit on the crease, not in a bubble. The leaf opens in the first cut.
 */
export const Fold07: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const cue = CUES.find((item) => t >= item.start && t < item.end) ?? CUES[CUES.length - 1];

  const open = interpolate(frame, [0, 42], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.out(Easing.quad),
  });
  const showName = clamp(frame, 120, 146);
  const showPercent = clamp(frame, 360, 378);
  const showBoss = clamp(frame, 540, 562);

  const fiber = (frame * 3) % 90;
  const breathe = Math.sin(frame * 0.05) * 7;
  const drift = Math.sin(frame * 0.063 + 0.8) * 6;
  const zoom = 1 + frame * 0.000024 + Math.sin(frame * 0.028) * 0.0045;
  const shadowX = 18 + Math.sin(frame * 0.046) * 12;
  const shadowY = 26 + Math.cos(frame * 0.039) * 10;
  const topExtra = TOP_FULL * open;
  const botExtra = BOT_FULL * open;
  const numScale = 1 - showPercent * 0.12 - showBoss * 0.08;
  const bossScale = 1 + showBoss * 0.14;
  const sheetTop = CREASE - BAND - topExtra;
  const sheetBottom = CREASE + BAND + botExtra;

  return (
    <AbsoluteFill style={{ backgroundColor: INK, overflow: "hidden" }}>
      <AbsoluteFill
        style={{
          backgroundImage:
            "radial-gradient(circle, rgba(246,226,122,0.22) 1px, transparent 1.7px)",
          backgroundSize: "26px 26px",
          backgroundPosition: `${fiber}px ${(fiber * 0.6) % 26}px`,
        }}
      />
      <AbsoluteFill style={{ transform: `scale(${zoom})`, transformOrigin: "50% 52%" }}>
        <div
          style={{
            position: "absolute",
            left: SHEET_L + shadowX,
            top: sheetTop + shadowY,
            width: SHEET_W,
            height: sheetBottom - sheetTop,
            backgroundColor: "#050505",
            opacity: 0.38,
          }}
        />

        <div
          style={{
            position: "absolute",
            left: SHEET_L,
            width: SHEET_W,
            top: sheetTop,
            height: topExtra,
            overflow: "hidden",
            backgroundColor: YELLOW,
            backgroundImage: `repeating-linear-gradient(${7 + Math.sin(frame * 0.02) * 2}deg, transparent 0 20px, rgba(36,36,36,0.05) 20px 21px)`,
            backgroundPosition: `${fiber}px 0px`,
            borderTop: `10px solid ${RIM}`,
            borderLeft: `10px solid ${RIM}`,
            borderRight: `10px solid ${RIM}`,
            boxSizing: "border-box",
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 0,
              width: "100%",
              bottom: 0,
              height: TOP_FULL,
              display: "flex",
              alignItems: "flex-start",
              justifyContent: "center",
              paddingTop: 28,
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "flex-end",
                justifyContent: "center",
                transform: `translateY(${breathe}px) scale(${numScale})`,
                color: INK,
                fontFamily,
              }}
            >
              <span style={{ fontSize: 230, lineHeight: 0.86, letterSpacing: -4 }}>0.36</span>
              <span
                style={{
                  fontSize: 86,
                  lineHeight: 1,
                  marginLeft: 10,
                  marginBottom: 22,
                  opacity: showPercent,
                  display: "inline-block",
                  transform: `translateY(${(1 - showPercent) * 18}px) scale(${0.86 + showPercent * 0.14})`,
                }}
              >
                %
              </span>
            </div>
          </div>
          <div
            style={{
              position: "absolute",
              right: 0,
              top: 0,
              width: 78,
              height: 78,
              backgroundColor: RIM,
              clipPath: "polygon(100% 0, 0 0, 100% 100%)",
              opacity: showPercent,
              transform: `translate(${(1 - showPercent) * 20}px, ${(1 - showPercent) * -12}px)`,
            }}
          />
        </div>

        <div
          style={{
            position: "absolute",
            left: SHEET_L,
            width: SHEET_W,
            top: CREASE + BAND,
            height: botExtra,
            overflow: "hidden",
            backgroundColor: INK,
            borderLeft: `10px solid ${YELLOW}`,
            borderRight: `10px solid ${YELLOW}`,
            borderBottom: `10px solid ${YELLOW}`,
            boxSizing: "border-box",
          }}
        >
          <div style={{ position: "absolute", left: 0, width: "100%", top: 0, height: BOT_FULL }}>
            <div
              style={{
                position: "absolute",
                left: "50%",
                top: 28 + drift,
                width: 520,
                height: 168,
                marginLeft: -260,
                borderRadius: 84,
                border: `9px solid ${YELLOW}`,
                opacity: 0.42 * showBoss,
                transform: `scale(${0.92 + showBoss * 0.08 + Math.sin(frame * 0.07) * 0.018})`,
              }}
            />
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: 48,
                textAlign: "center",
                color: YELLOW,
                fontFamily,
                fontSize: 128,
                lineHeight: 1,
                letterSpacing: 8,
                opacity: interpolate(open, [0.74, 0.96], [0, 1], {
                  extrapolateLeft: "clamp",
                  extrapolateRight: "clamp",
                }),
                transform: `translateY(${drift}px) scale(${bossScale})`,
              }}
            >
              事業主
            </div>
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: 268,
                display: "flex",
                justifyContent: "center",
                opacity: showName,
                transform: `translateY(${(1 - showName) * 36 + Math.sin(frame * 0.055) * 5}px) scale(${0.98 + showName * 0.02})`,
              }}
            >
              <Img
                src={staticFile("ira/building_kaisya.png")}
                style={{ width: 232, height: 256, objectFit: "contain" }}
              />
            </div>
          </div>
        </div>

        <div
          style={{
            position: "absolute",
            left: SHEET_L,
            width: SHEET_W,
            top: CREASE - BAND,
            height: BAND,
            backgroundColor: YELLOW,
            backgroundImage:
              "repeating-linear-gradient(90deg, transparent 0 16px, rgba(36,36,36,0.045) 16px 17px)",
            backgroundPosition: `${fiber}px 0`,
            borderLeft: `10px solid ${RIM}`,
            borderRight: `10px solid ${RIM}`,
            boxSizing: "border-box",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 3,
          }}
        >
          <div
            style={{
              color: INK,
              fontFamily,
              fontSize: 50,
              lineHeight: 1.15,
              textAlign: "center",
              whiteSpace: "nowrap",
              transform: `translateY(${Math.sin(frame * 0.08) * 1.4}px)`,
            }}
          >
            {cue.lines[0]}
          </div>
        </div>
        <div
          style={{
            position: "absolute",
            left: SHEET_L,
            width: SHEET_W,
            top: CREASE,
            height: BAND,
            backgroundColor: INK,
            borderLeft: `10px solid ${YELLOW}`,
            borderRight: `10px solid ${YELLOW}`,
            boxSizing: "border-box",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            zIndex: 3,
          }}
        >
          {cue.lines[1] ? (
            <div
              style={{
                color: YELLOW,
                fontFamily,
                fontSize: 50,
                lineHeight: 1.15,
                textAlign: "center",
                whiteSpace: "nowrap",
                transform: `translateY(${Math.sin(frame * 0.08 + 1.1) * 1.4}px)`,
              }}
            >
              {cue.lines[1]}
            </div>
          ) : null}
        </div>
        <div
          style={{
            position: "absolute",
            left: SHEET_L,
            width: SHEET_W,
            top: CREASE - 8,
            height: 16,
            zIndex: 4,
            backgroundImage: `linear-gradient(90deg, rgba(255,255,255,0.55), rgba(0,0,0,0.55) 42%, #111 50%, rgba(246,226,122,0.35) 58%, rgba(0,0,0,0.45))`,
            backgroundSize: "180% 100%",
            backgroundPosition: `${(frame * 5) % 200}px 0`,
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
