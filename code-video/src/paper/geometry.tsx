import type { ReactNode } from "react";

type Point = { x: number; y: number };

export const cubic = (a: Point, b: Point, c: Point, d: Point, t: number): Point => {
  const u = 1 - t;
  return {
    x: u * u * u * a.x + 3 * u * u * t * b.x + 3 * u * t * t * c.x + t * t * t * d.x,
    y: u * u * u * a.y + 3 * u * u * t * b.y + 3 * u * t * t * c.y + t * t * t * d.y,
  };
};

export const DottedCurve = ({
  from,
  c1,
  c2,
  to,
  progress,
  color,
  radius = 5.5,
  gap = 14,
  bead = false,
}: {
  from: Point;
  c1: Point;
  c2: Point;
  to: Point;
  progress: number;
  color: string;
  radius?: number;
  gap?: number;
  bead?: boolean;
}) => {
  const steps = 96;
  const samples: Array<Point & { d: number }> = [];
  let dist = 0;
  let prev = cubic(from, c1, c2, to, 0);
  for (let i = 0; i <= steps; i++) {
    const point = cubic(from, c1, c2, to, i / steps);
    if (i > 0) {
      dist += Math.hypot(point.x - prev.x, point.y - prev.y);
    }
    samples.push({ ...point, d: dist });
    prev = point;
  }

  const maxD = dist * Math.max(0, Math.min(1, progress));
  const dots: ReactNode[] = [];
  let index = 0;
  for (let d = 0; d <= maxD; d += gap) {
    let point = samples[0];
    for (const sample of samples) {
      if (sample.d >= d) {
        point = sample;
        break;
      }
    }
    dots.push(
      <circle
        key={index}
        cx={point.x}
        cy={point.y}
        r={radius}
        fill={bead && index % 2 === 1 ? "#f6f2ea" : color}
      />,
    );
    index += 1;
  }

  return <g>{dots}</g>;
};

const COS = Math.cos(Math.PI / 6);
const SIN = Math.sin(Math.PI / 6);

export const project = (x: number, y: number, z: number) => {
  return {
    x: (x - y) * COS,
    y: (x + y) * SIN - z,
  };
};

const pointsToPoly = (points: Point[]) => {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
};

export const IsoBox = ({
  x,
  y,
  z,
  w,
  d,
  h,
  top,
  left,
  right,
  origin,
  stroke,
}: {
  x: number;
  y: number;
  z: number;
  w: number;
  d: number;
  h: number;
  top: string;
  left: string;
  right: string;
  origin: Point;
  stroke?: string;
}) => {
  const at = (dx: number, dy: number, dz: number): Point => {
    const projected = project(x + dx, y + dy, z + dz);
    return { x: origin.x + projected.x, y: origin.y + projected.y };
  };
  const topFace = [at(0, 0, h), at(w, 0, h), at(w, d, h), at(0, d, h)];
  const rightFace = [at(w, 0, 0), at(w, d, 0), at(w, d, h), at(w, 0, h)];
  const leftFace = [at(0, d, 0), at(w, d, 0), at(w, d, h), at(0, d, h)];

  return (
    <g>
      <polygon points={pointsToPoly(leftFace)} fill={left} stroke={stroke} strokeWidth={stroke ? 2 : 0} />
      <polygon points={pointsToPoly(rightFace)} fill={right} stroke={stroke} strokeWidth={stroke ? 2 : 0} />
      <polygon points={pointsToPoly(topFace)} fill={top} stroke={stroke} strokeWidth={stroke ? 2 : 0} />
    </g>
  );
};

export const HAND_TIP = { x: 1096, y: 516 };

export const Tree = ({ x, y }: { x: number; y: number }) => {
  const lines: ReactNode[] = [];
  const grow = (
    sx: number,
    sy: number,
    angle: number,
    length: number,
    depth: number,
    seed: number,
  ) => {
    if (depth === 0 || length < 7) {
      return;
    }
    const ex = sx + Math.cos(angle) * length;
    const ey = sy + Math.sin(angle) * length;
    const wobble = ((seed * 13) % 9) / 18 - 0.25;
    lines.push(
      <line
        key={`${seed}-${depth}-${Math.round(sx)}-${Math.round(sy)}`}
        x1={sx}
        y1={sy}
        x2={ex}
        y2={ey}
        stroke="#2a2a2a"
        strokeWidth={Math.max(1.1, depth * 0.42)}
        strokeLinecap="round"
      />,
    );
    grow(ex, ey, angle - 0.48 + wobble, length * 0.74, depth - 1, seed + 3);
    grow(ex, ey, angle + 0.42 - wobble, length * 0.7, depth - 1, seed + 11);
  };
  grow(x, y, -Math.PI / 2, 78, 6, 2);
  return <g>{lines}</g>;
};

export const StandingFigure = ({
  x,
  y,
  scale = 1,
  color = "#1c1c1c",
}: {
  x: number;
  y: number;
  scale?: number;
  color?: string;
}) => {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`} fill={color}>
      <ellipse cx="0" cy="6" rx="16" ry="4" fill="#000" opacity="0.15" />
      <circle cx="0" cy="-58" r="9" />
      <path d="M-11 -48 Q0 -34 11 -48 L14 -8 Q8 8 0 10 Q-8 8 -14 -8 Z" />
    </g>
  );
};

export const CoatFigure = ({
  x,
  y,
  scale = 1,
  color = "#1a1420",
  hair = false,
}: {
  x: number;
  y: number;
  scale?: number;
  color?: string;
  hair?: boolean;
}) => {
  return (
    <g transform={`translate(${x} ${y}) scale(${scale})`} fill={color}>
      {hair ? (
        <ellipse cx="0" cy="-196" rx="36" ry="52" />
      ) : (
        <circle cx="0" cy="-188" r="30" />
      )}
      <rect x="-7" y="-162" width="14" height="20" rx="4" />
      <path d="M-58 -138 C-16 -150 16 -150 58 -138 L72 -8 L34 16 L20 -36 L0 22 L-20 -36 L-34 16 L-72 -8 Z" />
    </g>
  );
};
