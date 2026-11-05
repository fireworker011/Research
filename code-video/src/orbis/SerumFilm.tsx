import type { ReactNode } from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { DottedCurve } from "../paper/geometry";
import { mono, sans } from "../fonts";

export const SERUM_FPS = 30;
export const SERUM_WIDTH = 1080;
export const SERUM_HEIGHT = 1920;

const DRAW_FROM = 0;
const DRAW_DURATION = 180;
const BOTTLE_FROM = 180;
const BOTTLE_DURATION = 240;
const PALM_FROM = 420;
const PALM_DURATION = 180;
export const SERUM_DURATION = PALM_FROM + PALM_DURATION;

const ink = "#1c1c1c";
const muted = "#5e5a55";
const accent = "#9a3d32";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const tip = { x: 470, y: 1048 };

const threads = [
  {
    color: "#e10600",
    bead: true,
    delay: 12,
    c1: { x: 360, y: 980 },
    c2: { x: 180, y: 760 },
    to: { x: 90, y: 620 },
  },
  {
    color: "#2f6bff",
    bead: true,
    delay: 28,
    c1: { x: 340, y: 1120 },
    c2: { x: 160, y: 1280 },
    to: { x: 80, y: 1420 },
  },
  {
    color: "#f08a24",
    bead: false,
    delay: 40,
    c1: { x: 400, y: 1180 },
    c2: { x: 260, y: 1500 },
    to: { x: 140, y: 1620 },
  },
  {
    color: "#3aaa4a",
    bead: false,
    delay: 52,
    c1: { x: 500, y: 1200 },
    c2: { x: 420, y: 1480 },
    to: { x: 360, y: 1680 },
  },
] as const;

const Stage = ({ children }: { children: ReactNode }) => {
  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#efeae3",
        backgroundImage: `url(${staticFile("paper-noise.png")})`,
        backgroundSize: "180px 180px",
        backgroundBlendMode: "multiply",
        color: ink,
        fontFamily: sans,
      }}
    >
      {children}
    </AbsoluteFill>
  );
};

const FrameSvg = ({ children }: { children: ReactNode }) => {
  return (
    <svg viewBox="0 0 1080 1920" style={{ position: "absolute", inset: 0, width: 1080, height: 1920 }}>
      {children}
    </svg>
  );
};

const PointingHand = () => {
  return (
    <g>
      <path d="M860 900 L1180 820 L1180 1180 L900 1100 Z" fill="#8d8d95" />
      <ellipse cx="820" cy="1040" rx="170" ry="130" fill="#d8d8df" stroke="#2a2a2e" strokeWidth="5" />
      <rect x="430" y="1020" width="430" height="58" rx="29" fill="#d8d8df" stroke="#2a2a2e" strokeWidth="5" />
      <ellipse cx="930" cy="940" rx="40" ry="28" fill="#c0c0c8" stroke="#2a2a2e" strokeWidth="4" />
      <ellipse cx="980" cy="1020" rx="36" ry="26" fill="#c0c0c8" stroke="#2a2a2e" strokeWidth="4" />
      <ellipse cx="950" cy="1105" rx="34" ry="24" fill="#c0c0c8" stroke="#2a2a2e" strokeWidth="4" />
      <ellipse
        cx="720"
        cy="1160"
        rx="34"
        ry="58"
        transform="rotate(-28 720 1160)"
        fill="#c9c9d0"
        stroke="#2a2a2e"
        strokeWidth="4"
      />
      <ellipse cx="455" cy="1049" rx="14" ry="9" fill="#f4f4f6" />
    </g>
  );
};

const OpenPalm = () => {
  return (
    <g>
      <path d="M620 1180 L1180 1280 L1180 1520 L680 1460 Z" fill="#8d8d95" />
      <ellipse cx="560" cy="1280" rx="210" ry="160" fill="#d8d8df" stroke="#2a2a2e" strokeWidth="5" />
      <rect x="390" y="860" width="52" height="250" rx="26" transform="rotate(-14 416 985)" fill="#d8d8df" stroke="#2a2a2e" strokeWidth="5" />
      <rect x="470" y="800" width="52" height="280" rx="26" transform="rotate(-4 496 940)" fill="#d8d8df" stroke="#2a2a2e" strokeWidth="5" />
      <rect x="560" y="810" width="52" height="270" rx="26" transform="rotate(6 586 945)" fill="#d8d8df" stroke="#2a2a2e" strokeWidth="5" />
      <rect x="650" y="860" width="48" height="240" rx="24" transform="rotate(16 674 980)" fill="#d8d8df" stroke="#2a2a2e" strokeWidth="5" />
      <ellipse cx="390" cy="1360" rx="46" ry="78" transform="rotate(-40 390 1360)" fill="#c9c9d0" stroke="#2a2a2e" strokeWidth="5" />
    </g>
  );
};

const ShadedBottle = ({ y }: { y: number }) => {
  return (
    <g transform={`translate(390 ${y})`}>
      <rect x="108" y="0" width="84" height="36" rx="8" fill="#242428" />
      <rect x="124" y="36" width="52" height="48" fill="#3a3a40" />
      <path d="M70 90 H230 L210 150 H90 Z" fill="#efe4d6" stroke="#242428" strokeWidth="8" />
      <rect x="58" y="148" width="184" height="430" rx="36" fill="url(#glass)" stroke="#242428" strokeWidth="8" />
      <rect x="86" y="360" width="128" height="10" fill={accent} />
      <ellipse cx="120" cy="250" rx="18" ry="70" fill="#ffffff" opacity="0.45" />
    </g>
  );
};

export const DrawScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 70 } });
  const shift = interpolate(enter, [0, 1], [180, 0]);

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          top: 150,
          left: 72,
          zIndex: 2,
          fontFamily: mono,
          fontSize: 26,
          lineHeight: 1.55,
          letterSpacing: "0.08em",
          color: muted,
        }}
      >
        <div style={{ color: accent }}>広告</div>
        <div>FIG. 01</div>
        <div>夜の1本</div>
      </div>
      <FrameSvg>
        {threads.map((thread) => (
          <DottedCurve
            key={thread.color}
            from={tip}
            c1={thread.c1}
            c2={thread.c2}
            to={thread.to}
            progress={interpolate(frame, [thread.delay, thread.delay + 70], [0, 1], clamp)}
            color={thread.color}
            bead={thread.bead}
            radius={7}
            gap={16}
          />
        ))}
        <g transform={`translate(${shift} 0)`}>
          <PointingHand />
        </g>
      </FrameSvg>
    </Stage>
  );
};

export const BottleScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rise = spring({ frame, fps, config: { damping: 16, stiffness: 80 } });
  const label = interpolate(frame, [18, 36], [0, 1], clamp);

  return (
    <Stage>
      <div
        style={{
          position: "absolute",
          top: 120,
          left: 72,
          zIndex: 2,
          fontFamily: mono,
          fontSize: 26,
          color: accent,
          letterSpacing: "0.14em",
        }}
      >
        広告
      </div>
      <FrameSvg>
        <defs>
          <linearGradient id="glass" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#fffdf8" />
            <stop offset="55%" stopColor="#e4d3c0" />
            <stop offset="100%" stopColor="#a89078" />
          </linearGradient>
        </defs>
        <ellipse cx="540" cy="1120" rx="180" ry="28" fill="#000" opacity="0.08" />
        <ShadedBottle y={280 + (1 - rise) * 50} />
      </FrameSvg>
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          top: 1320,
          opacity: label,
        }}
      >
        <div style={{ fontFamily: mono, fontSize: 24, letterSpacing: "0.16em", color: accent }}>ORBIS</div>
        <div style={{ marginTop: 8, fontWeight: 900, fontSize: 54, letterSpacing: "-0.04em", lineHeight: 1.15 }}>
          ザ リンクルセラム
        </div>
        <div style={{ marginTop: 8, fontSize: 28, color: muted }}>医薬部外品 · 美容液</div>
        <div style={{ marginTop: 28, fontSize: 32, lineHeight: 1.45 }}>
          シワ改善 *1
          <br />
          美白 *2
        </div>
        <div style={{ marginTop: 16, fontSize: 24, lineHeight: 1.55, color: muted }}>
          *1 有効成分ナイアシンアミド
          <br />
          *2 メラニンの生成を抑え、シミ・そばかすを防ぐ
          <br />
          洗顔 → 化粧水 → この美容液 → 保湿
          <br />
          パール1粒
        </div>
      </div>
    </Stage>
  );
};

export const PalmScene = () => {
  const frame = useCurrentFrame();
  const fall = interpolate(frame, [8, 70], [0, 1], clamp);
  const dots = 14;

  return (
    <Stage>
      <FrameSvg>
        <OpenPalm />
        {Array.from({ length: dots }, (_, index) => {
          const t = index / (dots - 1);
          if (fall < t * 0.86) {
            return null;
          }
          const y = interpolate(t, [0, 1], [280, 1240]);
          const x = 560 + Math.sin(t * Math.PI) * 70;
          return <circle key={index} cx={x} cy={y} r={index === dots - 1 ? 16 : 8} fill="#e10600" />;
        })}
      </FrameSvg>
      <div
        style={{
          position: "absolute",
          left: 72,
          right: 72,
          bottom: 150,
          textAlign: "center",
          opacity: interpolate(frame, [50, 70], [0, 1], clamp),
        }}
      >
        <div style={{ fontWeight: 900, fontSize: 52, letterSpacing: "-0.04em" }}>詳しくはプロフィール</div>
        <div style={{ marginTop: 12, fontSize: 26, color: muted }}>オルビス ザ リンクルセラム · #PR · 広告</div>
      </div>
    </Stage>
  );
};

export const SerumFilm = () => {
  return (
    <AbsoluteFill>
      <Sequence from={DRAW_FROM} durationInFrames={DRAW_DURATION}>
        <DrawScene />
      </Sequence>
      <Sequence from={BOTTLE_FROM} durationInFrames={BOTTLE_DURATION}>
        <BottleScene />
      </Sequence>
      <Sequence from={PALM_FROM} durationInFrames={PALM_DURATION}>
        <PalmScene />
      </Sequence>
    </AbsoluteFill>
  );
};
