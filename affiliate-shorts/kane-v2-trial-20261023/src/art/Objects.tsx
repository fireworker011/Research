import { COIN, COIN_EDGE, INK, PAPER } from "../theme";
import { useFloat } from "../ui/motion";

export const BigPayslip: React.FC<{ readonly top?: number }> = ({ top = 150 }) => {
  const y = useFloat(6);
  return (
    <div style={{ position: "absolute", left: 230, top, transform: `translateY(${y}px)` }}>
      <svg width="620" height="460" viewBox="0 0 310 230">
        <rect x="8" y="8" width="294" height="214" rx="16" fill={PAPER} stroke={INK} strokeWidth="7" />
        <rect x="28" y="28" width="120" height="22" rx="6" fill="#E7D3A1" />
        <path
          d="M28 74 H270 M28 102 H250 M28 130 H230 M28 158 H200"
          stroke={INK}
          strokeWidth="6"
          strokeLinecap="round"
        />
        <circle cx="246" cy="168" r="28" fill={COIN} stroke={COIN_EDGE} strokeWidth="6" />
        <text
          x="246"
          y="178"
          textAnchor="middle"
          fontSize="28"
          fontFamily="sans-serif"
          fill={INK}
        >
          ¥
        </text>
      </svg>
    </div>
  );
};

export const CoinPile: React.FC<{
  readonly left: number;
  readonly top: number;
  readonly count: number;
}> = ({ left, top, count }) => {
  const y = useFloat(5);
  const coins = Array.from({ length: count }, (_, index) => index);
  return (
    <div style={{ position: "absolute", left, top, transform: `translateY(${y}px)` }}>
      <svg width="280" height="220" viewBox="0 0 140 110">
        {coins.map((index) => (
          <ellipse
            key={index}
            cx="70"
            cy={88 - index * 16}
            rx="48"
            ry="16"
            fill={index % 2 === 0 ? COIN : "#F6D56A"}
            stroke={COIN_EDGE}
            strokeWidth="5"
          />
        ))}
      </svg>
    </div>
  );
};

export const CalendarBoard: React.FC<{
  readonly label: string;
  readonly top?: number;
}> = ({ label, top = 160 }) => {
  const y = useFloat(6);
  return (
    <div style={{ position: "absolute", left: 250, top, transform: `translateY(${y}px)` }}>
      <svg width="580" height="460" viewBox="0 0 290 230">
        <rect x="8" y="8" width="274" height="214" rx="18" fill={PAPER} stroke={INK} strokeWidth="7" />
        <rect x="8" y="8" width="274" height="52" rx="18" fill="#E23B3B" />
        <rect x="8" y="36" width="274" height="24" fill="#E23B3B" />
        <circle cx="48" cy="28" r="8" fill={PAPER} />
        <circle cx="242" cy="28" r="8" fill={PAPER} />
        <text
          x="145"
          y="160"
          textAnchor="middle"
          fontSize="84"
          fontFamily="sans-serif"
          fill={INK}
        >
          {label}
        </text>
      </svg>
    </div>
  );
};

export const YearTrack: React.FC = () => {
  const y = useFloat(6);
  return (
    <div style={{ position: "absolute", left: 90, top: 220, transform: `translateY(${y}px)` }}>
      <svg width="900" height="280" viewBox="0 0 450 140">
        <path
          d="M40 78 H410"
          stroke={INK}
          strokeWidth="8"
          strokeLinecap="round"
        />
        <circle cx="70" cy="78" r="28" fill="#79B7E8" stroke={INK} strokeWidth="6" />
        <circle cx="225" cy="78" r="36" fill="#F0C14A" stroke={INK} strokeWidth="6" />
        <circle cx="380" cy="78" r="28" fill="#E08962" stroke={INK} strokeWidth="6" />
      </svg>
    </div>
  );
};
