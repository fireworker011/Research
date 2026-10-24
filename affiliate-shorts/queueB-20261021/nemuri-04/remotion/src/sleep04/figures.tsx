import {
  BG,
  CX,
  FIG_LEFT,
  FIG_TOP,
  HOVER_CY,
  INK,
  LINE,
  MATTRESS_Y,
  PILLOW_RX,
  VB_H,
  VB_W,
} from "./theme";

const curve = (y: number, drop: number) => {
  const mid = y + drop;
  return `M 150 ${y} Q ${CX} ${mid} 850 ${y}`;
};

export const GapFigure = ({
  frame,
  gap,
  sag,
  enter,
  slide,
  bracket,
  mattressOpacity,
  archOpacity,
  pillowRx,
  pillowRy,
}: {
  frame: number;
  gap: number;
  sag: number;
  enter: number;
  slide: number;
  bracket: number;
  mattressOpacity: number;
  archOpacity: number;
  pillowRx: number;
  pillowRy: number;
}) => {
  const zoom = 1 + (frame / 1019) * 0.045;
  const bob = Math.sin(frame / 36) * 5;
  const breath = Math.sin(frame / 17);
  const drop = sag * 78;
  const midY = MATTRESS_Y + drop;
  const rx = pillowRx + breath * 3;
  const ry = pillowRy + Math.cos(frame / 19) * 1.3;
  const settledCy = midY - 18 - ry;
  const cy = HOVER_CY + (settledCy - HOVER_CY) * enter + breath * 1.2;
  const top = cy - ry;
  const air = 18 + gap * 210;
  const peak = top - air;
  const px = CX + slide;
  const arch = `M ${px - rx} ${top - 12} Q ${px} ${peak} ${px + rx} ${top - 12}`;

  return (
    <div
      style={{
        position: "absolute",
        left: FIG_LEFT,
        top: FIG_TOP + bob,
        width: VB_W,
        height: VB_H,
        transform: `scale(${zoom})`,
        transformOrigin: "50% 48%",
      }}
    >
      <svg width={VB_W} height={VB_H} viewBox={`0 0 ${VB_W} ${VB_H}`}>
        <path
          d={curve(MATTRESS_Y, drop)}
          fill="none"
          stroke={LINE}
          strokeWidth={16}
          strokeLinecap="round"
          opacity={mattressOpacity}
        />
        <path
          d={curve(MATTRESS_Y + 22, drop)}
          fill="none"
          stroke={INK}
          strokeWidth={4}
          strokeLinecap="round"
          opacity={mattressOpacity * 0.5}
        />
        <path
          d={arch}
          fill="none"
          stroke={LINE}
          strokeWidth={8}
          strokeLinecap="round"
          opacity={archOpacity}
        />
        <ellipse cx={px} cy={cy} rx={rx} ry={ry} fill={BG} />
        <ellipse
          cx={px}
          cy={cy}
          rx={rx}
          ry={ry}
          fill={LINE}
          fillOpacity={0.28}
          stroke={LINE}
          strokeWidth={12}
        />
        <ellipse
          cx={px}
          cy={cy}
          rx={Math.max(12, rx - 22)}
          ry={Math.max(8, ry - 16)}
          fill="none"
          stroke={INK}
          strokeWidth={3}
          opacity={0.4}
        />
        {bracket > 0.02 ? (
          <g opacity={bracket}>
            <line
              x1={868}
              y1={midY}
              x2={868}
              y2={peak}
              stroke={INK}
              strokeWidth={4}
            />
            <line x1={850} y1={midY} x2={886} y2={midY} stroke={INK} strokeWidth={4} />
            <line x1={850} y1={peak} x2={886} y2={peak} stroke={INK} strokeWidth={4} />
          </g>
        ) : null}
      </svg>
    </div>
  );
};

export const OpeningFigure = ({ frame }: { frame: number }) => {
  const zoom = 1 + (frame / 1019) * 0.045;
  const bob = Math.sin(frame / 36) * 5;
  const breath = Math.sin(frame / 15);
  const rx =
    (frame < 60
      ? 16 + (frame / 60) * (PILLOW_RX + 70 - 16)
      : frame < 120
        ? PILLOW_RX + 70 - ((frame - 60) / 60) * 40
        : frame < 180
          ? PILLOW_RX + 30 - ((frame - 120) / 60) * 24
          : PILLOW_RX + 6 - ((frame - 180) / 60) * 6) + breath;
  const ry =
    (frame < 60
      ? 6 + (frame / 60) * 3
      : frame < 120
        ? 9 + ((frame - 60) / 60) * 34
        : frame < 180
          ? 43 + ((frame - 120) / 60) * 19
          : 62) + (frame > 45 ? breath * 0.8 : 0);
  const mattressOpacity = frame < 180 ? 0 : Math.min(1, (frame - 180) / 30) * 0.75;
  const ring = frame < 168 ? 0 : Math.min(1, (frame - 168) / 24) * 0.4;

  return (
    <div
      style={{
        position: "absolute",
        left: FIG_LEFT,
        top: FIG_TOP + bob,
        width: VB_W,
        height: VB_H,
        transform: `scale(${zoom})`,
        transformOrigin: "50% 48%",
      }}
    >
      <svg width={VB_W} height={VB_H} viewBox={`0 0 ${VB_W} ${VB_H}`}>
        <path
          d={curve(MATTRESS_Y, 0)}
          fill="none"
          stroke={LINE}
          strokeWidth={16}
          strokeLinecap="round"
          opacity={mattressOpacity}
        />
        <ellipse
          cx={CX}
          cy={HOVER_CY}
          rx={Math.max(8, rx)}
          ry={Math.max(4, ry)}
          fill={BG}
        />
        <ellipse
          cx={CX}
          cy={HOVER_CY}
          rx={Math.max(8, rx)}
          ry={Math.max(4, ry)}
          fill={LINE}
          fillOpacity={frame < 70 ? 0.12 : 0.28}
          stroke={LINE}
          strokeWidth={12}
        />
        {ring > 0.02 ? (
          <ellipse
            cx={CX}
            cy={HOVER_CY}
            rx={Math.max(12, rx - 22)}
            ry={Math.max(8, ry - 16)}
            fill="none"
            stroke={INK}
            strokeWidth={3}
            opacity={ring}
          />
        ) : null}
      </svg>
    </div>
  );
};
