import { interpolate } from "remotion";
import {
  BATH_END,
  DAY_END,
  GOLD,
  INK,
  NAVY,
  OPEN_END,
  ROOM_END,
  breath,
  clamp,
  mixHex,
} from "./theme";

const Label = ({
  text,
  top,
  size,
  opacity,
  fontFamily,
  left = 80,
  width = 920,
}: {
  text: string;
  top: number;
  size: number;
  opacity: number;
  fontFamily: string;
  left?: number;
  width?: number;
}) => {
  if (opacity <= 0.02) {
    return null;
  }
  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width,
        textAlign: "center",
        fontFamily,
        fontWeight: 700,
        fontSize: size,
        lineHeight: 1.1,
        color: INK,
        opacity,
        whiteSpace: "nowrap",
      }}
    >
      {text}
    </div>
  );
};

const Glow = ({ frame }: { frame: number }) => {
  const x = 540 + Math.sin(frame / 27) * 240;
  const room = frame >= DAY_END && frame < ROOM_END;
  const y = room ? 1560 + Math.cos(frame / 34) * 40 : 1180 + Math.cos(frame / 34) * 70;
  const color = room ? "rgba(58, 82, 122, 0.55)" : "rgba(240, 195, 106, 0.30)";
  return (
    <div
      style={{
        position: "absolute",
        left: x - 300,
        top: y - 300,
        width: 600,
        height: 600,
        borderRadius: "50%",
        background: `radial-gradient(circle, ${color} 0%, transparent 70%)`,
      }}
    />
  );
};

const Opening = ({ frame }: { frame: number }) => {
  const p = interpolate(frame, [6, 58], [0, 1], clamp);
  const x = 460 + p * 90;
  const y = 1210 - p * 260;
  const r = 22 + p * 58;
  const line = interpolate(frame, [0, 26], [0, 1], clamp);
  const ray = interpolate(frame, [34, 50], [0, 1], clamp);
  const spin = (frame * 0.6 * Math.PI) / 180;
  return (
    <g>
      <line
        x1={140}
        y1={1288}
        x2={140 + 800 * line}
        y2={1288}
        stroke={INK}
        strokeWidth={breath(frame, 6, 1)}
        strokeLinecap="round"
      />
      <g transform={`translate(${x} ${y}) rotate(${(spin * 180) / Math.PI})`}>
        <circle r={r} fill={GOLD} />
        {Array.from({ length: 8 }, (_, i) => {
          const angle = (i / 8) * Math.PI * 2 + spin;
          const inner = r + 10;
          const outer = r + 26;
          return (
            <line
              key={i}
              x1={Math.cos(angle) * inner}
              y1={Math.sin(angle) * inner}
              x2={Math.cos(angle) * outer}
              y2={Math.sin(angle) * outer}
              stroke={GOLD}
              strokeWidth={5}
              strokeLinecap="round"
              opacity={ray}
            />
          );
        })}
      </g>
    </g>
  );
};

const Day = ({ frame }: { frame: number }) => {
  const local = frame - OPEN_END;
  const along = interpolate(local, [0, 150], [0, 1], clamp);
  const angle = Math.PI + along * Math.PI;
  const sunX = 540 + Math.cos(angle) * 286;
  const sunY = 1128 + Math.sin(angle) * 286;
  const hand = Math.PI * 0.85 + along * Math.PI * 0.7;
  const hx = Math.cos(hand) * 108;
  const hy = Math.sin(hand) * 108;
  const stroke = breath(frame, 8, 1.1);
  return (
    <g>
      <g transform="translate(540 1128)">
        <circle r={156} fill="none" stroke={INK} strokeWidth={stroke} />
        <circle r={104} fill="none" stroke={INK} strokeWidth={3} opacity={0.55} />
        {Array.from({ length: 12 }, (_, i) => {
          const tick = (i / 12) * Math.PI * 2;
          return (
            <line
              key={i}
              x1={Math.cos(tick) * 132}
              y1={Math.sin(tick) * 132}
              x2={Math.cos(tick) * 148}
              y2={Math.sin(tick) * 148}
              stroke={INK}
              strokeWidth={4}
              strokeLinecap="round"
            />
          );
        })}
        <line
          x1={0}
          y1={0}
          x2={hx}
          y2={hy}
          stroke={GOLD}
          strokeWidth={8}
          strokeLinecap="round"
        />
        <circle r={12} fill={GOLD} />
      </g>
      <g transform={`translate(${sunX} ${sunY})`}>
        <circle r={46} fill={GOLD} />
        {Array.from({ length: 8 }, (_, i) => {
          const ray = (i / 8) * Math.PI * 2 + frame * 0.01;
          return (
            <line
              key={i}
              x1={Math.cos(ray) * 56}
              y1={Math.sin(ray) * 56}
              x2={Math.cos(ray) * 74}
              y2={Math.sin(ray) * 74}
              stroke={GOLD}
              strokeWidth={5}
              strokeLinecap="round"
            />
          );
        })}
      </g>
    </g>
  );
};

const Room = ({ frame }: { frame: number }) => {
  const local = frame - DAY_END;
  const darken = interpolate(local, [0, 78], [0, 1], clamp);
  const glass = mixHex(GOLD, NAVY, darken);
  const slash = interpolate(local, [16, 46], [160, 0], clamp);
  const floatY = Math.sin(local / 18) * 8;
  const ring = breath(frame, 8, 1);
  return (
    <g>
      <rect
        x={120}
        y={790}
        width={380}
        height={420}
        rx={22}
        fill={glass}
        stroke={INK}
        strokeWidth={breath(frame, 10, 1)}
      />
      <line x1={310} y1={800} x2={310} y2={1200} stroke={INK} strokeWidth={8} />
      <line x1={132} y1={1000} x2={488} y2={1000} stroke={INK} strokeWidth={8} />
      <g transform={`translate(620 ${830 + floatY})`}>
        <rect
          x={0}
          y={0}
          width={250}
          height={360}
          rx={36}
          fill={NAVY}
          stroke={INK}
          strokeWidth={8}
        />
        <rect x={92} y={22} width={66} height={10} rx={5} fill={INK} opacity={0.8} />
        <circle cx={125} cy={190} r={78} fill="none" stroke={GOLD} strokeWidth={ring} />
        <line
          x1={70}
          y1={136}
          x2={180}
          y2={246}
          stroke={GOLD}
          strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={160}
          strokeDashoffset={slash}
        />
      </g>
    </g>
  );
};

const steamPath = (x: number, y: number) =>
  `M ${x - 22} ${y + 28} Q ${x} ${y - 8} ${x + 22} ${y + 24}`;

const Bath = ({ frame }: { frame: number }) => {
  const local = frame - ROOM_END;
  const water = 0.72 + Math.sin(frame / 11) * 0.16;
  const span = 0.5 + Math.sin(local / 22) * 0.5;
  const dotX = 500 + span * 320;
  return (
    <g>
      {Array.from({ length: 3 }, (_, i) => {
        const cycle = ((frame * 0.55 + i * 18) % 52) / 52;
        const rise = cycle * 96;
        const x = 430 + (i - 1) * 58;
        const y = 860 - rise;
        return (
          <path
            key={i}
            d={steamPath(x, y)}
            fill="none"
            stroke={INK}
            strokeWidth={breath(frame, 4, 0.6)}
            strokeLinecap="round"
            opacity={Math.sin(cycle * Math.PI) * 0.8}
          />
        );
      })}
      <rect
        x={210}
        y={860}
        width={460}
        height={188}
        rx={94}
        fill="#18243A"
        stroke={INK}
        strokeWidth={breath(frame, 8, 1)}
      />
      <ellipse cx={440} cy={930} rx={176} ry={34} fill="#3E6C8C" opacity={water} />
      <line
        x1={160}
        y1={1310}
        x2={930}
        y2={1310}
        stroke={INK}
        strokeWidth={6}
        strokeLinecap="round"
      />
      <line
        x1={500}
        y1={1310}
        x2={820}
        y2={1310}
        stroke={GOLD}
        strokeWidth={16}
        strokeLinecap="round"
      />
      <circle cx={dotX} cy={1310} r={13} fill={INK} />
      <circle cx={984} cy={1310} r={26} fill={INK} />
      <circle cx={998} cy={1298} r={22} fill={NAVY} />
    </g>
  );
};

const Close = ({ frame }: { frame: number }) => {
  const local = frame - BATH_END;
  const turn = local * 4;
  const orbit = (local / 60) * Math.PI * 2;
  const x = 540 + Math.cos(orbit - Math.PI / 2) * 168;
  const y = 1088 + Math.sin(orbit - Math.PI / 2) * 168;
  const circ = 2 * Math.PI * 168;
  const gap = circ * 0.14;
  return (
    <g>
      <circle
        cx={540}
        cy={1088}
        r={168}
        fill="none"
        stroke={INK}
        strokeWidth={breath(frame, 8, 1)}
        strokeDasharray={`${circ - gap} ${gap}`}
        strokeDashoffset={-turn}
        strokeLinecap="round"
      />
      <circle cx={x} cy={y} r={34} fill={GOLD} />
    </g>
  );
};

export const Stage = ({ frame, fontFamily }: { frame: number; fontFamily: string }) => {
  const dayLocal = frame - OPEN_END;
  const roomLocal = frame - DAY_END;
  const bathLocal = frame - ROOM_END;
  const dayLabel =
    frame >= OPEN_END && frame < DAY_END
      ? interpolate(dayLocal, [14, 32], [0, 1], clamp) *
        interpolate(dayLocal, [136, 150], [1, 0], clamp)
      : 0;
  const roomLabel =
    frame >= DAY_END && frame < ROOM_END
      ? interpolate(roomLocal, [72, 90], [0, 1], clamp) *
        interpolate(roomLocal, [136, 150], [1, 0], clamp)
      : 0;
  const bathLabel =
    frame >= ROOM_END && frame < BATH_END
      ? interpolate(bathLocal, [18, 36], [0, 1], clamp) *
        interpolate(bathLocal, [136, 150], [1, 0], clamp)
      : 0;

  return (
    <>
      <Glow frame={frame} />
      <svg
        width={1080}
        height={1920}
        viewBox="0 0 1080 1920"
        style={{ position: "absolute", inset: 0 }}
      >
        {frame < OPEN_END ? <Opening frame={frame} /> : null}
        {frame >= OPEN_END && frame < DAY_END ? <Day frame={frame} /> : null}
        {frame >= DAY_END && frame < ROOM_END ? <Room frame={frame} /> : null}
        {frame >= ROOM_END && frame < BATH_END ? <Bath frame={frame} /> : null}
        {frame >= BATH_END ? <Close frame={frame} /> : null}
      </svg>
      <Label text="体内時計" top={1364} size={64} opacity={dayLabel} fontFamily={fontFamily} />
      <Label text="暗く" top={1288} size={72} opacity={roomLabel} fontFamily={fontFamily} />
      <Label
        text="1〜2時間"
        top={1148}
        size={60}
        opacity={bathLabel}
        fontFamily={fontFamily}
        left={360}
        width={600}
      />
    </>
  );
};
