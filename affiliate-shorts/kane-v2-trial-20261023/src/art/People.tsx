import { INK, PAPER, SKIN, BLUSH } from "../theme";
import { useFloat } from "../ui/motion";

const stroke = {
  fill: "none" as const,
  stroke: INK,
  strokeWidth: 6,
  strokeLinejoin: "round" as const,
  strokeLinecap: "round" as const,
};

const Face: React.FC<{ readonly hair: string }> = ({ hair }) => {
  return (
    <g>
      <ellipse cx="86" cy="176" rx="18" ry="22" fill={SKIN} stroke={INK} strokeWidth="5" />
      <ellipse cx="314" cy="176" rx="18" ry="22" fill={SKIN} stroke={INK} strokeWidth="5" />
      <ellipse cx="200" cy="172" rx="96" ry="104" fill={SKIN} stroke={INK} strokeWidth="6" />
      <path
        d="M118 150 C118 78 160 62 200 62 C240 62 282 78 282 150 C250 132 226 124 200 124 C174 124 150 132 118 150 Z"
        fill={hair}
        stroke={INK}
        strokeWidth="6"
        strokeLinejoin="round"
      />
      <ellipse cx="162" cy="166" rx="9" ry="11" fill={INK} />
      <ellipse cx="238" cy="166" rx="9" ry="11" fill={INK} />
      <circle cx="165" cy="162" r="3" fill="#fff" />
      <circle cx="241" cy="162" r="3" fill="#fff" />
      <path d="M194 188 Q200 202 210 190" fill="none" stroke="#E09A84" strokeWidth="4" strokeLinecap="round" />
      <path d="M172 218 Q200 236 228 218" fill="none" stroke={INK} strokeWidth="6" strokeLinecap="round" />
      <ellipse cx="136" cy="200" rx="16" ry="9" fill={BLUSH} />
      <ellipse cx="264" cy="200" rx="16" ry="9" fill={BLUSH} />
    </g>
  );
};

const Body: React.FC<{ readonly shirt: string }> = ({ shirt }) => {
  return (
    <g>
      <path d="M188 258 H212 V292 H188 Z" fill={SKIN} stroke={INK} strokeWidth="5" />
      <path
        d="M112 292 C150 270 250 270 288 292 L324 400 H76 Z"
        fill={shirt}
        stroke={INK}
        strokeWidth="6"
        strokeLinejoin="round"
      />
    </g>
  );
};

const Payslip: React.FC = () => {
  return (
    <g transform="translate(286 286) rotate(-8)">
      <rect x="0" y="0" width="128" height="96" rx="8" fill={PAPER} stroke={INK} strokeWidth="5" />
      <rect x="12" y="14" width="46" height="8" rx="3" fill="#E7D3A1" />
      <path d="M12 38 H108 M12 52 H96 M12 66 H80" {...stroke} strokeWidth="4" />
    </g>
  );
};

const MonthCard: React.FC = () => {
  return (
    <g transform="translate(278 278)">
      <rect x="0" y="0" width="120" height="100" rx="8" fill={PAPER} stroke={INK} strokeWidth="5" />
      <rect x="0" y="0" width="120" height="24" rx="8" fill="#E23B3B" />
      <rect x="0" y="14" width="120" height="12" fill="#E23B3B" />
      <circle cx="28" cy="52" r="5" fill={INK} />
      <circle cx="60" cy="52" r="5" fill={INK} />
      <circle cx="92" cy="52" r="5" fill={INK} />
      <circle cx="28" cy="76" r="5" fill={INK} />
      <circle cx="60" cy="76" r="5" fill={INK} />
      <circle cx="92" cy="76" r="5" fill={INK} />
    </g>
  );
};

export const Person: React.FC<{
  readonly hair: string;
  readonly shirt: string;
  readonly hold: "payslip" | "calendar" | "none";
  readonly top: number;
  readonly width?: number;
}> = ({ hair, shirt, hold, top, width = 640 }) => {
  const y = useFloat(8);
  const left = (1080 - width) / 2;

  return (
    <div
      style={{
        position: "absolute",
        left,
        top,
        width,
        transform: `translateY(${y}px)`,
      }}
    >
      <svg viewBox="0 0 420 420" width="100%" height="100%">
        <ellipse cx="210" cy="392" rx="110" ry="16" fill="rgba(58,42,34,0.12)" />
        <g transform="translate(10 8)">
          <Body shirt={shirt} />
          <Face hair={hair} />
          {hold === "payslip" ? <Payslip /> : null}
          {hold === "calendar" ? <MonthCard /> : null}
        </g>
      </svg>
    </div>
  );
};
