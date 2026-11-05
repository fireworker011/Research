import React from "react";
import {
  AbsoluteFill,
  Img,
  continueRender,
  delayRender,
  interpolate,
  staticFile,
  useCurrentFrame,
} from "remotion";
import { loadFont } from "@remotion/google-fonts/ShipporiMincho";

const { fontFamily, waitUntilDone } = loadFont("normal", {
  weights: ["700"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});
const fontHandle = delayRender("shippori-mincho-ledger09");
waitUntilDone().then(() => {
  continueRender(fontHandle);
});

const PAPER = "#E4D7F0";
const NOTE = "#FFFCF7";
const RULE = "#9C88B8";
const INK = "#3A2E52";

const appear = (frame: number, start: number) =>
  interpolate(frame, [start, start + 28], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const Rules: React.FC<{ top: number; count: number; gap: number }> = ({ top, count, gap }) => (
  <>
    {Array.from({ length: count }, (_, index) => (
      <div
        key={index}
        style={{
          position: "absolute",
          left: 18,
          right: 18,
          top: top + index * gap,
          height: 2,
          backgroundColor: RULE,
          opacity: 0.85,
        }}
      />
    ))}
  </>
);

/**
 * A pale-purple ledger. The wide column is the bonus field.
 * The camera eases into that column. No caption layer.
 * No people. No sample payslip amounts.
 */
export const Ledger09: React.FC = () => {
  const frame = useCurrentFrame();
  const approach = interpolate(frame, [0, 240, 1499], [1, 1.045, 1.055], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const scale = approach + Math.sin(frame / 27) * 0.0028;
  const driftX = Math.sin(frame / 43) * 3.5;
  const driftY = Math.sin(frame / 32) * 6;
  const shadowX = 12 + Math.sin(frame / 25) * 6;
  const shadowY = 20 + Math.cos(frame / 29) * 5;
  const sheen = 180 + Math.sin(frame / 70) * 260;

  const pension = appear(frame, 246);
  const standard = appear(frame, 300);
  const trim = appear(frame, 486);
  const cap = appear(frame, 726);
  const over = appear(frame, 996);
  const child = appear(frame, 1266);
  const strike = interpolate(frame, [540, 610], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const chipDrop = interpolate(frame, [610, 700], [0, 22], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const capWidth = interpolate(frame, [726, 800], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const amountFloat = Math.sin(frame / 17) * 5;

  return (
    <AbsoluteFill style={{ backgroundColor: "#D9C7EB", overflow: "hidden", fontFamily, fontWeight: 700, color: INK }}>
      <AbsoluteFill
        style={{
          backgroundImage:
            "repeating-linear-gradient(90deg, rgba(156,136,184,0.16) 0 2px, transparent 2px 86px)",
          opacity: 0.45,
        }}
      />
      <div
        style={{
          position: "absolute",
          left: 58,
          top: 132,
          width: 964,
          height: 1260,
          transformOrigin: "64% 18%",
          transform: `translate(${driftX}px, ${driftY}px) scale(${scale})`,
          backgroundColor: PAPER,
          border: `4px solid ${RULE}`,
          boxShadow: `${shadowX}px ${shadowY}px 34px rgba(62, 40, 92, 0.2)`,
          overflow: "hidden",
        }}
      >
        <div style={{ position: "absolute", left: 0, top: 0, bottom: 0, width: 42, backgroundColor: RULE }} />
        <div style={{ position: "absolute", left: 42, top: 0, bottom: 0, width: 10, backgroundColor: "#CDB6E4" }} />
        {[0, 1].map((column) => (
          <div
            key={column}
            style={{
              position: "absolute",
              left: 78 + column * 86,
              top: 28,
              bottom: 28,
              width: 70,
              borderLeft: `2px solid ${RULE}`,
              borderRight: `2px solid ${RULE}`,
            }}
          >
            <Rules top={70} count={13} gap={86} />
          </div>
        ))}
        <div
          style={{
            position: "absolute",
            left: 252,
            top: 22,
            right: 22,
            bottom: 22,
            border: `3px solid ${RULE}`,
            backgroundColor: PAPER,
          }}
        >
          <div
            style={{
              position: "absolute",
              left: 0,
              right: 0,
              top: 0,
              height: 168,
              backgroundColor: "#EFE4F6",
              borderBottom: `3px solid ${RULE}`,
            }}
          />
          <div style={{ position: "absolute", left: 36, top: 18, fontSize: 34, letterSpacing: 6, color: RULE }}>
            欄
          </div>
          <div style={{ position: "absolute", left: 36, top: 52, fontSize: 108, lineHeight: 1, letterSpacing: 10 }}>
            賞与
          </div>
          <Rules top={210} count={8} gap={112} />
          <div
            style={{
              position: "absolute",
              left: sheen,
              top: -40,
              width: 90,
              height: 1400,
              background: "linear-gradient(90deg, transparent, rgba(255,252,247,0.45), transparent)",
              transform: "rotate(8deg)",
            }}
          />

          <div
            style={{
              position: "absolute",
              left: 36,
              top: 236,
              opacity: pension,
              transform: `translateY(${(1 - pension) * 14}px)`,
              fontSize: 48,
            }}
          >
            厚生年金
          </div>
          <div
            style={{
              position: "absolute",
              left: 36,
              top: 348,
              opacity: standard,
              transform: `translateY(${(1 - standard) * 14 + Math.sin(frame / 21) * 2}px)`,
              fontSize: 48,
            }}
          >
            標準賞与額
          </div>

          <div
            style={{
              position: "absolute",
              left: 36,
              top: 462,
              opacity: trim,
              display: "flex",
              alignItems: "center",
              gap: 18,
            }}
          >
            <div style={{ fontSize: 44 }}>千円未満</div>
            <div style={{ position: "relative", width: 132, height: 36, transform: `translateY(${chipDrop}px)` }}>
              {[0, 1, 2].map((index) => (
                <div
                  key={index}
                  style={{
                    position: "absolute",
                    left: index * 42,
                    top: 4,
                    width: 28,
                    height: 28,
                    border: `3px solid ${RULE}`,
                    backgroundColor: NOTE,
                  }}
                />
              ))}
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  top: 16,
                  height: 4,
                  width: `${strike * 120}px`,
                  backgroundColor: INK,
                }}
              />
            </div>
            <div style={{ fontSize: 44 }}>切り捨て</div>
          </div>

          <div
            style={{
              position: "absolute",
              left: 28,
              right: 28,
              top: 676,
              opacity: cap,
            }}
          >
            <div style={{ fontSize: 30, letterSpacing: 2, marginBottom: 8 }}>一ヶ月の上限</div>
            <div style={{ height: 8, width: `${capWidth}%`, backgroundColor: RULE }} />
          </div>
          <div
            style={{
              position: "absolute",
              left: 36,
              top: 792,
              opacity: cap,
              fontSize: 64,
              lineHeight: 1,
              letterSpacing: 2,
              transform: `translateY(${amountFloat}px)`,
            }}
          >
            百五十万円
          </div>

          <div
            style={{
              position: "absolute",
              left: 28,
              right: 28,
              top: 562,
              height: 78,
              opacity: over * 0.9,
              backgroundImage: `repeating-linear-gradient(-45deg, transparent, transparent 8px, rgba(156,136,184,0.55) 8px, rgba(156,136,184,0.55) 12px)`,
              display: "flex",
              alignItems: "center",
              paddingLeft: 8,
              fontSize: 32,
            }}
          >
            超えた分
          </div>
          <div
            style={{
              position: "absolute",
              left: 36,
              top: 908,
              opacity: over,
              transform: `translateY(${Math.sin(frame / 24) * 2}px)`,
              fontSize: 44,
            }}
          >
            計算の土台
          </div>
          <div
            style={{
              position: "absolute",
              left: 36,
              top: 1020,
              right: 24,
              opacity: child,
              transform: `translateY(${(1 - child) * 16}px)`,
              fontSize: 36,
              lineHeight: 1.15,
            }}
          >
            子ども・子育て拠出金
            <div style={{ fontSize: 32, marginTop: 10 }}>同じ上限</div>
          </div>

        </div>
      </div>

      <Img
        src={staticFile("ira/kane09_ledger.png")}
        style={{
          position: "absolute",
          left: 28,
          top: 1548,
          width: 168,
          height: 148,
          objectFit: "contain",
          transform: `translateY(${Math.sin(frame / 30) * 4}px)`,
        }}
      />
      <Img
        src={staticFile("ira/kane09_envelope.png")}
        style={{
          position: "absolute",
          left: 200,
          top: 1564,
          width: 92,
          height: 120,
          objectFit: "contain",
          transform: `translateY(${Math.sin(frame / 26 + 1) * 5}px)`,
        }}
      />
      <Img
        src={staticFile("ira/kane09_paybag.png")}
        style={{
          position: "absolute",
          left: 292,
          top: 1576,
          width: 118,
          height: 108,
          objectFit: "contain",
          transform: `translateY(${Math.sin(frame / 23 + 2) * 4}px)`,
        }}
      />
    </AbsoluteFill>
  );
};
