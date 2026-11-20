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
import { loadFont } from "@remotion/google-fonts/BIZUDPGothic";

const { fontFamily, waitUntilDone } = loadFont("normal", {
  weights: ["700"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});
const fontHandle = delayRender("biz-udp-gothic-scale08");
waitUntilDone().then(() => {
  continueRender(fontHandle);
});

const PAPER = "#F7F8FA";
const NAVY = "#1D3557";
const RED = "#E63946";

/** Body cues only. The last SRT cue is replaced by the end card. */
const CUES: { start: number; end: number; lines: string[] }[] = [
  { start: 0, end: 3.2, lines: ["片道、二キロ未満。"] },
  { start: 3.2, end: 6.6, lines: ["マイカーと自転車。"] },
  { start: 6.6, end: 10.4, lines: ["通勤手当は"] },
  { start: 10.4, end: 14.6, lines: ["全額、課税。"] },
  { start: 14.6, end: 19.0, lines: ["令和八年四月の表でも", "同じ。"] },
  { start: 19.0, end: 23.4, lines: ["二キロ以上は"] },
  { start: 23.4, end: 27.4, lines: ["距離で限度が変わる。"] },
  { start: 27.4, end: 31.0, lines: ["駐車場は、別の条件。"] },
];

const AXIS_X = 168;
const SCALE_BOTTOM = 1488;
const SCALE_TOP = 268;
const SPAN = SCALE_BOTTOM - SCALE_TOP;

const CAR_W = 430;
const CAR_H = Math.round((CAR_W * 588) / 809);
const BIKE_W = 352;
const BIKE_H = Math.round((BIKE_W * 609) / 780);
const PARK_W = 404;
const PARK_H = Math.round((PARK_W * 915) / 1077);

const MARKS = [
  { km: 0, label: "0" },
  { km: 0.5, label: "" },
  { km: 1, label: "1" },
  { km: 1.5, label: "" },
  { km: 2, label: "2" },
];

const yAt = (km: number) => SCALE_BOTTOM - (km / 2) * SPAN;

const clamp01 = (
  frame: number,
  from: number,
  to: number,
  easing: (input: number) => number = Easing.linear,
) =>
  interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing,
  });

/**
 * A vertical 0–2 km ruler grows up from the floor.
 * A car and a bicycle climb it. The 2 km cap is the only red.
 * Captions sit in the lower right, in a gothic face.
 */
export const Scale08: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / 30;
  const cue = CUES.find((item) => t >= item.start && t < item.end) ?? CUES[CUES.length - 1];

  const grow = clamp01(frame, 0, 90, Easing.inOut(Easing.cubic));
  const grownTop = SCALE_BOTTOM - SPAN * grow;
  const climb = interpolate(frame, [96, 760], [0.32, 1.7], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
    easing: Easing.inOut(Easing.cubic),
  });
  const bob = Math.sin(frame * 0.11) * 9;
  const carKm = climb + Math.sin(frame * 0.047) * 0.025;
  const bikeKm = Math.max(0.16, climb - 0.52) + Math.cos(frame * 0.053) * 0.02;
  const carY = yAt(carKm) + bob;
  const bikeY = yAt(bikeKm) - bob * 0.6;
  const riders = clamp01(frame, 96, 118);
  const taxWash = clamp01(frame, 312, 348) * (1 - clamp01(frame, 560, 600) * 0.45);
  const sheet = clamp01(frame, 438, 468) * (1 - clamp01(frame, 570, 600));
  const over = clamp01(frame, 570, 604);
  const park = clamp01(frame, 822, 852, Easing.out(Easing.cubic));
  const zoom = 1 + frame * 0.00002 + Math.sin(frame * 0.02) * 0.003;
  const shadowX = 16 + Math.sin(frame * 0.05) * 10;
  const shadowY = 22 + Math.cos(frame * 0.041) * 8;
  const labelLift = Math.sin(frame * 0.07) * 3;
  const dotX = (frame * 0.45) % 32;
  const dotY = (frame * 0.28) % 32;
  const glint = (frame * 7) % (SPAN + 80);

  return (
    <AbsoluteFill style={{ backgroundColor: PAPER, overflow: "hidden", fontFamily }}>
      <AbsoluteFill
        style={{
          backgroundImage: `radial-gradient(circle, rgba(29,53,87,0.16) 1.1px, transparent 1.4px)`,
          backgroundSize: "32px 32px",
          backgroundPosition: `${dotX}px ${dotY}px`,
        }}
      />
      <AbsoluteFill style={{ transform: `scale(${zoom})`, transformOrigin: "22% 62%" }}>
        <div
          style={{
            position: "absolute",
            left: AXIS_X - 18 + shadowX * 0.3,
            top: grownTop + shadowY * 0.25,
            width: 36,
            height: SCALE_BOTTOM - grownTop,
            backgroundColor: NAVY,
            opacity: 0.08,
            borderRadius: 18,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: AXIS_X - 7,
            top: grownTop,
            width: 14,
            height: Math.max(0, SCALE_BOTTOM - grownTop),
            backgroundColor: NAVY,
            borderRadius: 7,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 0,
              width: "100%",
              height: 70,
              top: SPAN - glint,
              background: "linear-gradient(to bottom, transparent, rgba(247,248,250,0.85), transparent)",
            }}
          />
        </div>
        <div
          style={{
            position: "absolute",
            left: AXIS_X - 34,
            top: grownTop,
            width: 68,
            height: Math.max(0, SCALE_BOTTOM - grownTop),
            backgroundColor: RED,
            opacity: 0.13 * taxWash,
          }}
        />
        {MARKS.map((mark) => {
          if (mark.km / 2 > grow + 0.001) {
            return null;
          }
          const y = yAt(mark.km) + (mark.km === 2 ? 0 : labelLift * (mark.km === 0 ? -1 : 1));
          const red = mark.km === 2;
          return (
            <div key={mark.km}>
              <div
                style={{
                  position: "absolute",
                  left: AXIS_X - (red ? 36 : 24),
                  top: y - (red ? 4 : 2),
                  width: red ? 72 : 48,
                  height: red ? 8 : 4,
                  backgroundColor: red ? RED : NAVY,
                  borderRadius: 3,
                }}
              />
              {mark.label ? (
                <div
                  style={{
                    position: "absolute",
                    left: 36,
                    top: y - 28,
                    width: 90,
                    textAlign: "right",
                    color: red ? RED : NAVY,
                    fontFamily,
                    fontWeight: 700,
                    fontSize: red ? 54 : 40,
                    lineHeight: 1,
                  }}
                >
                  {mark.label}
                </div>
              ) : null}
            </div>
          );
        })}
        {grow > 0.995 ? (
          <div
            style={{
              position: "absolute",
              left: AXIS_X + 28,
              top: yAt(2) - 18 + labelLift,
              color: RED,
              fontFamily,
              fontWeight: 700,
              fontSize: 28,
              letterSpacing: 1,
            }}
          >
            km
          </div>
        ) : null}
        {[0, 1, 2].map((index) => {
          const width = 70 + ((frame * 0.55 + index * 48) % 110);
          return (
            <div
              key={index}
              style={{
                position: "absolute",
                left: AXIS_X + 48,
                top: SCALE_TOP - 46 - index * 42,
                width,
                height: 8,
                borderRadius: 4,
                backgroundColor: NAVY,
                opacity: 0.55 * over,
              }}
            />
          );
        })}

        <Img
          src={staticFile("ira/kane08_car.png")}
          style={{
            position: "absolute",
            left: 214,
            top: carY - CAR_H / 2,
            width: CAR_W,
            height: CAR_H,
            opacity: riders,
            filter: `drop-shadow(${shadowX}px ${shadowY}px 0 rgba(29,53,87,0.18))`,
          }}
        />
        <Img
          src={staticFile("ira/kane08_bicycle.png")}
          style={{
            position: "absolute",
            left: 690,
            top: bikeY - BIKE_H / 2,
            width: BIKE_W,
            height: BIKE_H,
            opacity: riders,
            filter: `drop-shadow(${shadowX * 0.7}px ${shadowY}px 0 rgba(29,53,87,0.16))`,
          }}
        />

        <div
          style={{
            position: "absolute",
            left: 640 + shadowX,
            top: 300 + shadowY,
            width: 360,
            height: 230,
            backgroundColor: NAVY,
            opacity: 0.12 * sheet,
            borderRadius: 6,
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 628,
            top: 286 + (1 - sheet) * 24,
            width: 360,
            height: 230,
            backgroundColor: "#FFFFFF",
            border: `4px solid ${NAVY}`,
            borderRadius: 6,
            opacity: sheet,
            overflow: "hidden",
          }}
        >
          {[0, 1, 2, 3].map((row) => (
            <div
              key={row}
              style={{
                position: "absolute",
                left: 28,
                right: 28,
                top: 42 + row * 44,
                height: 6,
                backgroundColor: NAVY,
                opacity: 0.35,
                width: `${70 + ((frame + row * 17) % 24)}%`,
              }}
            />
          ))}
        </div>

        <div
          style={{
            position: "absolute",
            left: 612 + (1 - park) * 50 + shadowX * 0.4,
            top: 1040 + shadowY * 0.4,
            width: PARK_W + 28,
            height: PARK_H + 28,
            border: `4px dashed ${NAVY}`,
            borderRadius: 12,
            opacity: park,
          }}
        />
        <Img
          src={staticFile("ira/kane08_parking.png")}
          style={{
            position: "absolute",
            left: 626 + (1 - park) * 50,
            top: 1054 + Math.sin(frame * 0.06) * 5,
            width: PARK_W,
            height: PARK_H,
            opacity: park,
          }}
        />
      </AbsoluteFill>

      <div
        style={{
          position: "absolute",
          right: 44,
          bottom: 108 + Math.sin(frame * 0.05) * 2,
          maxWidth: 760,
          textAlign: "right",
          color: NAVY,
          fontFamily,
          fontWeight: 700,
          fontSize: 52,
          lineHeight: 1.32,
          backgroundColor: "rgba(247,248,250,0.94)",
          padding: "16px 26px 18px",
          borderRight: `10px solid ${NAVY}`,
          borderRadius: 4,
        }}
      >
        {cue.lines.map((line) => (
          <div key={line}>{line}</div>
        ))}
      </div>
    </AbsoluteFill>
  );
};
