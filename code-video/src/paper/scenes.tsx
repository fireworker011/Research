import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from "remotion";
import {
  CoatFigure,
  DottedCurve,
  HAND_TIP,
  IsoBox,
  StandingFigure,
  Tree,
} from "./geometry";
import { Caption, Fig, Paper } from "./ui";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const threads = [
  {
    color: "#e10600",
    bead: true,
    delay: 8,
    c1: { x: 980, y: 460 },
    c2: { x: 520, y: 760 },
    to: { x: 140, y: 640 },
  },
  {
    color: "#2f6bff",
    bead: true,
    delay: 28,
    c1: { x: 1040, y: 300 },
    c2: { x: 640, y: 180 },
    to: { x: 220, y: 340 },
  },
  {
    color: "#f08a24",
    bead: false,
    delay: 40,
    c1: { x: 1100, y: 560 },
    c2: { x: 760, y: 820 },
    to: { x: 360, y: 860 },
  },
  {
    color: "#3aaa4a",
    bead: false,
    delay: 52,
    c1: { x: 1180, y: 620 },
    c2: { x: 980, y: 900 },
    to: { x: 620, y: 920 },
  },
  {
    color: "#c43bd0",
    bead: true,
    delay: 60,
    c1: { x: 1280, y: 540 },
    c2: { x: 1180, y: 780 },
    to: { x: 900, y: 820 },
  },
] as const;

export const DrawScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 18, stiffness: 70 } });
  const shift = interpolate(enter, [0, 1], [240, 0]);
  const tip = HAND_TIP;

  return (
    <Paper>
      <Fig n="01" title="紙の上で引く" />
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        {threads.map((thread) => {
          const progress = interpolate(frame, [thread.delay, thread.delay + 78], [0, 1], clamp);
          return (
            <DottedCurve
              key={thread.color}
              from={tip}
              c1={thread.c1}
              c2={thread.c2}
              to={thread.to}
              progress={progress}
              color={thread.color}
              bead={thread.bead}
            />
          );
        })}
      </svg>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transform: `translateX(${shift}px)`,
        }}
      >
        <div
          style={{
            position: "absolute",
            left: 1580,
            top: 470,
            width: 380,
            height: 160,
            background: "#7a7a82",
            clipPath: "polygon(0% 18%, 100% 0%, 100% 100%, 6% 72%)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 1320,
            top: 430,
            width: 230,
            height: 180,
            borderRadius: "50%",
            background: "#d4d4da",
            border: "4px solid #3c3c42",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 1040,
            top: 490,
            width: 320,
            height: 52,
            borderRadius: 26,
            background: "#d4d4da",
            border: "4px solid #3c3c42",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 1470,
            top: 400,
            width: 58,
            height: 42,
            borderRadius: 21,
            background: "#b4b4ba",
            border: "3px solid #3c3c42",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 1510,
            top: 455,
            width: 54,
            height: 40,
            borderRadius: 20,
            background: "#b4b4ba",
            border: "3px solid #3c3c42",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 1488,
            top: 520,
            width: 50,
            height: 38,
            borderRadius: 19,
            background: "#b4b4ba",
            border: "3px solid #3c3c42",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 1288,
            top: 545,
            width: 78,
            height: 100,
            borderRadius: 40,
            background: "#c4c4ca",
            border: "3px solid #3c3c42",
            transform: "rotate(-32deg)",
          }}
        />
      </div>
    </Paper>
  );
};

export const RedScene = () => {
  return (
    <Paper background="#e10600" grain={false}>
      <Caption text="ほどけた" color="#fffaf6" bottom={86} />
    </Paper>
  );
};

const petals = Array.from({ length: 28 }, (_, index) => {
  return {
    x: (index * 197) % 1920,
    base: (index * 83) % 1080,
    speed: 0.55 + (index % 5) * 0.22,
    r: 3 + (index % 3),
    color: ["#f3b4c4", "#e89ab8", "#f6d2cc", "#d9c6ee"][index % 4],
  };
});

const IslandBody = ({
  cx,
  cy,
  scale,
  tree,
  leftFigure,
  rightFigure,
}: {
  cx: number;
  cy: number;
  scale: number;
  tree: boolean;
  leftFigure: boolean;
  rightFigure: boolean;
}) => {
  return (
    <g transform={`translate(${cx} ${cy}) scale(${scale})`}>
      <ellipse cx="0" cy="36" rx="210" ry="28" fill="#000" opacity="0.08" />
      <path d="M-190 0 A190 190 0 0 0 190 0 Z" fill="url(#islandShade)" />
      <ellipse cx="0" cy="0" rx="190" ry="52" fill="#f7f4ef" />
      {tree ? <Tree x={-40} y={-8} /> : null}
      {leftFigure ? <StandingFigure x={-18} y={-6} scale={0.72} /> : null}
      {rightFigure ? <StandingFigure x={70} y={-4} scale={0.72} /> : null}
    </g>
  );
};

export const IslandScene = () => {
  const frame = useCurrentFrame();
  const split = interpolate(frame, [78, 150], [0, 1], clamp);
  const bob = Math.sin(frame / 18) * 8;

  return (
    <Paper>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <defs>
          <linearGradient id="islandShade" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f4c2d0" />
            <stop offset="55%" stopColor="#d7c4ee" />
            <stop offset="100%" stopColor="#b7c4ee" />
          </linearGradient>
        </defs>
        {petals.map((petal, index) => (
          <circle
            key={index}
            cx={petal.x}
            cy={(petal.base + frame * petal.speed) % 1080}
            r={petal.r}
            fill={petal.color}
            opacity="0.8"
          />
        ))}
        <g opacity={1 - split}>
          <IslandBody cx={960} cy={500 + bob} scale={1} tree leftFigure rightFigure />
        </g>
        <g opacity={split}>
          <IslandBody
            cx={960 - split * 430}
            cy={470 + bob}
            scale={0.78}
            tree
            leftFigure
            rightFigure={false}
          />
          <IslandBody
            cx={960 + split * 430}
            cy={540 - bob}
            scale={0.9}
            tree={false}
            leftFigure={false}
            rightFigure
          />
          <line
            x1={960 - split * 250}
            y1={470}
            x2={960 + split * 250}
            y2={500}
            stroke="#8d8880"
            strokeWidth={2}
            strokeDasharray="2 8"
            opacity={split}
          />
        </g>
      </svg>
      <Caption text="離れていく" />
    </Paper>
  );
};

export const NightScene = () => {
  const frame = useCurrentFrame();
  const trainX = interpolate(frame, [0, 120], [-260, 1500], clamp);

  return (
    <AbsoluteFill style={{ background: "#142033" }}>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <path d="M0 640 L280 430 L520 560 L780 360 L1100 520 L1420 390 L1920 560 L1920 1080 L0 1080 Z" fill="#1c2c44" />
        <path d="M0 700 L360 520 L700 640 L1040 470 L1500 620 L1920 540 L1920 1080 L0 1080 Z" fill="#243650" />
        <rect x="0" y="760" width="1920" height="140" fill="#1a2436" />
        <rect x="0" y="812" width="1920" height="8" fill="#8ea0b8" opacity="0.35" />
        <g transform={`translate(${trainX} 760)`}>
          <rect x="-180" y="18" width="520" height="10" fill="url(#trail)" opacity="0.9" />
          {Array.from({ length: 7 }, (_, index) => (
            <rect
              key={index}
              x={index * 36}
              y="8"
              width="28"
              height="22"
              rx="3"
              fill={["#ff5a7a", "#ffb703", "#8bd450", "#49a0ff", "#7a5cff", "#ff7ad9", "#fff1c9"][index]}
            />
          ))}
        </g>
        {Array.from({ length: 80 }, (_, index) => {
          const speed = 2.2 + (index % 6) * 0.45;
          const x = (index * 47) % 1920;
          const y = ((index * 29) + frame * speed) % 980;
          return <circle key={index} cx={x} cy={y} r={1 + (index % 3) * 0.6} fill="#f4f7fb" opacity="0.75" />;
        })}
        <defs>
          <linearGradient id="trail" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#ff5a7a" stopOpacity="0" />
            <stop offset="40%" stopColor="#ffd166" />
            <stop offset="70%" stopColor="#69d2ff" />
            <stop offset="100%" stopColor="#ffffff" />
          </linearGradient>
        </defs>
      </svg>
      <AbsoluteFill style={{ background: "linear-gradient(#000, #0000 18%, #0000 82%, #000)" }} />
    </AbsoluteFill>
  );
};

const boxes = [
  { x: -30, y: -24, z: 0, w: 250, d: 200, h: 18, top: "#f2c14e", left: "#1c1c1c", right: "#111", delay: 0 },
  { x: 8, y: 8, z: 18, w: 72, d: 72, h: 78, top: "#7ec8ff", left: "#3d8fd4", right: "#2f6ea8", delay: 4 },
  { x: 92, y: 16, z: 18, w: 64, d: 58, h: 52, top: "#9be7ff", left: "#5ec4ea", right: "#3aa4d4", delay: 8 },
  { x: 12, y: 96, z: 18, w: 60, d: 58, h: 86, top: "#8ee07a", left: "#46b85a", right: "#2f8d42", delay: 10 },
  { x: 100, y: 92, z: 18, w: 96, d: 52, h: 40, top: "#ff8d8d", left: "#e25b5b", right: "#c43e3e", delay: 12 },
] as const;

export const CityScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const origin = { x: 820, y: 700 };

  return (
    <Paper>
      <Fig n="02" title="組み立て" />
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <line x1="-40" y1="860" x2="1680" y2="280" stroke="#e10600" strokeWidth="34" strokeLinecap="square" />
        <line x1="180" y1="980" x2="1980" y2="220" stroke="#2f6bff" strokeWidth="26" strokeLinecap="square" />
        {boxes.map((box) => {
          const rise = spring({
            frame: frame - box.delay,
            fps,
            config: { damping: 15, stiffness: 80 },
          });
          return (
            <IsoBox
              key={`${box.x}-${box.y}-${box.top}`}
              x={box.x}
              y={box.y}
              z={box.z}
              w={box.w}
              d={box.d}
              h={box.h * rise}
              top={box.top}
              left={box.left}
              right={box.right}
              origin={origin}
            />
          );
        })}
        {Array.from({ length: 8 }, (_, index) => {
          const rise = spring({
            frame: frame - 14,
            fps,
            config: { damping: 16, stiffness: 70 },
          });
          const pink = index % 2 === 0;
          return (
            <IsoBox
              key={`tower-${index}`}
              x={78}
              y={48}
              z={18 + index * 26 * rise}
              w={46}
              d={46}
              h={26 * rise}
              top={pink ? "#ff4f9a" : "#ffe14a"}
              left={pink ? "#e2317c" : "#f0b429"}
              right={pink ? "#c41862" : "#d49212"}
              origin={origin}
            />
          );
        })}
        <IsoBox
          x={168}
          y={24}
          z={18}
          w={62}
          d={70}
          h={96 * spring({ frame: frame - 18, fps, config: { damping: 16, stiffness: 80 } })}
          top="none"
          left="none"
          right="none"
          stroke="#1a1a1a"
          origin={origin}
        />
        <g transform="translate(1540 560)">
          <rect x="-8" y="30" width="16" height="280" fill="#1a1a1a" />
          <g transform="rotate(38)">
            <rect x="-110" y="-16" width="220" height="32" rx="3" fill="#1a1a1a" />
            <rect x="-92" y="-16" width="28" height="32" fill="#f2c14e" />
            <rect x="-28" y="-16" width="28" height="32" fill="#f2c14e" />
            <rect x="36" y="-16" width="28" height="32" fill="#f2c14e" />
          </g>
          <g transform="rotate(-38)">
            <rect x="-110" y="-16" width="220" height="32" rx="3" fill="#1a1a1a" />
            <rect x="-92" y="-16" width="28" height="32" fill="#f2c14e" />
            <rect x="-28" y="-16" width="28" height="32" fill="#f2c14e" />
            <rect x="36" y="-16" width="28" height="32" fill="#f2c14e" />
          </g>
          <circle cx="-34" cy="130" r="18" fill="#e10600" />
          <circle cx="34" cy="130" r="18" fill="#e10600" />
        </g>
        <StandingFigure x={1660} y={760} scale={0.9} />
      </svg>
    </Paper>
  );
};

export const PairScene = () => {
  const frame = useCurrentFrame();
  const gap = interpolate(frame, [8, 70], [90, 340], clamp);
  const line = interpolate(frame, [0, 36], [0, 1], clamp);

  return (
    <AbsoluteFill
      style={{
        background:
          "radial-gradient(circle at 30% 40%, #f3c7b8 0%, transparent 42%), radial-gradient(circle at 70% 45%, #c9d4f8 0%, transparent 46%), linear-gradient(#efe6ea, #d5d3e4)",
      }}
    >
      <svg width="1920" height="1080" viewBox="0 0 1920 1080">
        <defs>
          <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="18" />
          </filter>
          <linearGradient id="pairLine" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#ff5a7a" />
            <stop offset="35%" stopColor="#ffe14a" />
            <stop offset="68%" stopColor="#49e07a" />
            <stop offset="100%" stopColor="#4aa0ff" />
          </linearGradient>
        </defs>
        <g filter="url(#soft)" opacity="0.85">
          <ellipse cx="520" cy="420" rx="340" ry="220" fill="#f7b7a8" />
          <ellipse cx="1380" cy="460" rx="380" ry="240" fill="#b9c6f5" />
        </g>
        <line
          x1={960 - 760 * line}
          y1="560"
          x2={960 + 760 * line}
          y2="560"
          stroke="url(#pairLine)"
          strokeWidth="10"
        />
        <CoatFigure x={960 - gap} y={760} scale={1.7} hair />
        <CoatFigure x={960 + gap} y={760} scale={1.8} color="#24182c" />
      </svg>
    </AbsoluteFill>
  );
};

export const PalmScene = () => {
  const frame = useCurrentFrame();
  const fall = interpolate(frame, [8, 70], [0, 1], clamp);
  const tint = interpolate(frame, [90, 130], [0, 1], clamp);
  const fill = tint > 0.5 ? "#d7c4e4" : "#c8c8cd";
  const arc = 12;

  return (
    <Paper>
      <div style={{ position: "absolute", inset: 0 }}>
        <div
          style={{
            position: "absolute",
            left: 1280,
            top: 560,
            width: 520,
            height: 180,
            background: fill === "#c8c8cd" ? "#7a7a82" : "#6d6278",
            clipPath: "polygon(0% 22%, 100% 8%, 100% 88%, 4% 70%)",
          }}
        />
        {[
          { left: 980, top: 300, rotate: -16 },
          { left: 1060, top: 270, rotate: -4 },
          { left: 1140, top: 285, rotate: 8 },
          { left: 1210, top: 330, rotate: 18 },
        ].map((finger) => (
          <div
            key={finger.left}
            style={{
              position: "absolute",
              left: finger.left,
              top: finger.top,
              width: 46,
              height: 190,
              borderRadius: 23,
              background: fill,
              border: "4px solid #3c3c42",
              transform: `rotate(${finger.rotate}deg)`,
            }}
          />
        ))}
        <div
          style={{
            position: "absolute",
            left: 1040,
            top: 430,
            width: 280,
            height: 210,
            borderRadius: "50%",
            background: fill,
            border: "4px solid #3c3c42",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: 960,
            top: 560,
            width: 90,
            height: 130,
            borderRadius: 45,
            background: "#b7b7be",
            border: "4px solid #3c3c42",
            transform: "rotate(-36deg)",
          }}
        />
      </div>
      <svg width="1920" height="1080" viewBox="0 0 1920 1080" style={{ position: "absolute", inset: 0 }}>
        {Array.from({ length: arc }, (_, index) => {
          const t = index / (arc - 1);
          if (fall < t * 0.82) {
            return null;
          }
          const y = interpolate(t, [0, 1], [120, 640]);
          const x = 1160 + Math.sin(t * Math.PI) * 80;
          return <circle key={index} cx={x} cy={y} r={index === arc - 1 ? 8 : 5.5} fill="#e10600" />;
        })}
      </svg>
      <Caption text="まだ、ここにある" />
    </Paper>
  );
};
