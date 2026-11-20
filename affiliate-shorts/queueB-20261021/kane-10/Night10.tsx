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
import { loadFont } from "@remotion/google-fonts/ZenMaruGothic";

const { fontFamily, waitUntilDone } = loadFont("normal", {
  weights: ["700"],
  subsets: ["japanese", "latin"],
  ignoreTooManyRequestsWarning: true,
});
const fontHandle = delayRender("zen-maru-night10");
waitUntilDone().then(() => {
  continueRender(fontHandle);
});

const NAVY = "#101828";
const CREAM = "#F4F1EA";
const GOLD = "#E8C872";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const rise = (frame: number, start: number, dur = 12) =>
  interpolate(frame, [start, start + dur], [0, 1], clamp);

const section = (frame: number, start: number, end: number) =>
  Math.min(
    rise(frame, start, 12),
    interpolate(frame, [end - 12, end], [1, 0], clamp),
  );

const grow = (frame: number, start: number, dur: number) =>
  interpolate(frame, [start, start + dur], [0, 1], clamp);

const RateRow: React.FC<{ label: string; rate: string; fill: number }> = ({
  label,
  rate,
  fill,
}) => (
  <div style={{ display: "flex", alignItems: "center", gap: 16, height: 78 }}>
    <div style={{ width: 156, fontSize: 42, lineHeight: 1.2, whiteSpace: "nowrap" }}>{label}</div>
    <div style={{ width: 236, fontSize: 48, lineHeight: 1.2, whiteSpace: "nowrap" }}>{rate}</div>
    <div
      style={{
        flex: 1,
        height: 22,
        borderRadius: 11,
        backgroundColor: "rgba(16,24,40,0.12)",
        overflow: "hidden",
      }}
    >
      <div
        style={{
          width: `${Math.max(0, Math.min(1, fill)) * 100}%`,
          height: "100%",
          backgroundColor: NAVY,
          boxSizing: "border-box",
          borderRight: fill > 0.04 ? `8px solid ${GOLD}` : "none",
        }}
      />
    </div>
  </div>
);

/**
 * Night clock for the 22:00–5:00 premium.
 * Top third is a navy band with the time only.
 * No subtitle layer. Illustrations stay at one scale, uncropped.
 */
export const Night10: React.FC = () => {
  const frame = useCurrentFrame();
  const zoom = 1 + interpolate(frame, [0, 809], [0, 0.012], clamp) + Math.sin(frame / 23) * 0.0035;
  const driftX = Math.sin(frame / 43) * 3;
  const driftY = Math.cos(frame / 37) * 3;
  const floatY = Math.sin(frame / 18) * 4;
  const numberBob = 1 + Math.sin(frame / 19) * 0.012;

  const light22 = rise(frame, 0, 20);
  const light5 = rise(frame, 28, 26);
  const principal = interpolate(frame, [690, 720], [1, 0], clamp);
  const shifted = rise(frame, 716, 28);
  const ruleW = interpolate(frame, [16, 46], [0, 168], clamp) + Math.sin(frame / 15) * 6;

  const night = section(frame, 135, 270);
  const premium = section(frame, 270, 405);
  const overtime = section(frame, 405, 540);
  const holiday = section(frame, 540, 675);
  const region = rise(frame, 675, 12);

  const nightFill = grow(frame, 156, 64);
  const premiumFill = grow(frame, 300, 56);
  const overA = grow(frame, 424, 40);
  const overB = grow(frame, 456, 40);
  const overSum = rise(frame, 452, 14);
  const holiA = grow(frame, 560, 42);
  const holiB = grow(frame, 592, 40);
  const holiSum = rise(frame, 580, 14);
  const arrow = grow(frame, 704, 48);

  return (
    <AbsoluteFill style={{ backgroundColor: CREAM, overflow: "hidden", fontFamily, fontWeight: 700, color: NAVY }}>
      <div
        style={{
          position: "absolute",
          inset: 0,
          transformOrigin: "50% 46%",
          transform: `translate(${driftX}px, ${driftY}px) scale(${zoom})`,
        }}
      >
        <div style={{ position: "absolute", left: 0, right: 0, top: 0, height: 640, backgroundColor: NAVY, overflow: "hidden" }}>
          <div
            style={{
              position: "absolute",
              top: 0,
              bottom: 0,
              width: 74,
              left: (frame * 5) % 1280 - 120,
              background: "linear-gradient(90deg, transparent, rgba(244,241,234,0.10), transparent)",
            }}
          />
          {[0, 1, 2].map((dot) => (
            <div
              key={dot}
              style={{
                position: "absolute",
                width: 7,
                height: 7,
                borderRadius: 4,
                backgroundColor: GOLD,
                left: 72 + dot * 28 + Math.sin(frame / 27 + dot) * 8,
                top: 52 + Math.cos(frame / 22 + dot) * 7,
              }}
            />
          ))}
          <div
            style={{
              position: "absolute",
              right: 76,
              top: 214 + Math.sin(frame / 31) * 6,
              width: 150,
              height: 190,
            }}
          >
            <Img
              src={staticFile("ira/kane10_moon.png")}
              style={{ width: 150, height: 190, objectFit: "contain" }}
            />
          </div>
          <div style={{ position: "absolute", left: 0, right: 210, top: 118, textAlign: "center", color: CREAM }}>
            <div style={{ position: "relative", height: 176 }}>
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: 0,
                  fontSize: 156,
                  lineHeight: 1.05,
                  opacity: light22 * principal,
                  transform: `translateY(${floatY}px) scale(${numberBob * (0.94 + 0.06 * light22)})`,
                }}
              >
                22:00
              </div>
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: 0,
                  fontSize: 156,
                  lineHeight: 1.05,
                  opacity: shifted,
                  transform: `translateY(${floatY}px) scale(${numberBob})`,
                }}
              >
                23:00
              </div>
            </div>
            <div style={{ width: Math.max(0, ruleW), height: 4, margin: "6px auto 12px", backgroundColor: GOLD }} />
            <div style={{ position: "relative", height: 156 }}>
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: 0,
                  fontSize: 136,
                  lineHeight: 1.05,
                  opacity: light5 * principal,
                  transform: `translateY(${Math.sin(frame / 21) * 4}px) scale(${numberBob})`,
                }}
              >
                5:00
              </div>
              <div
                style={{
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: 0,
                  fontSize: 136,
                  lineHeight: 1.05,
                  opacity: shifted,
                  transform: `translateY(${Math.sin(frame / 21) * 4}px) scale(${numberBob})`,
                }}
              >
                6:00
              </div>
            </div>
          </div>
        </div>

        <div style={{ position: "absolute", left: 88, right: 88, top: 760, height: 500 }}>
          <div style={{ position: "absolute", inset: 0, opacity: night }}>
            <div style={{ paddingTop: 54, textAlign: "center", fontSize: 76, lineHeight: 1.2, transform: `translateY(${floatY}px)` }}>
              深夜
            </div>
            <div style={{ marginTop: 42, height: 26, borderRadius: 13, backgroundColor: "rgba(16,24,40,0.12)", overflow: "hidden" }}>
              <div style={{ width: `${nightFill * 100}%`, height: "100%", backgroundColor: NAVY, position: "relative" }}>
                {nightFill > 0.04 ? (
                  <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: 10, backgroundColor: GOLD }} />
                ) : null}
              </div>
            </div>
          </div>

          <div style={{ position: "absolute", inset: 0, opacity: premium }}>
            <div style={{ paddingTop: 20, textAlign: "center", fontSize: 40, lineHeight: 1.2 }}>割増</div>
            <div style={{ marginTop: 18, textAlign: "center", fontSize: 78, lineHeight: 1.2, transform: `translateY(${floatY}px)` }}>
              二割五分以上
            </div>
            <div style={{ marginTop: 40, height: 26, borderRadius: 13, backgroundColor: "rgba(16,24,40,0.12)", overflow: "hidden" }}>
              <div style={{ width: `${premiumFill * 0.42 * 100}%`, height: "100%", backgroundColor: NAVY, position: "relative" }}>
                {premiumFill > 0.04 ? (
                  <div style={{ position: "absolute", right: 0, top: 0, bottom: 0, width: 10, backgroundColor: GOLD }} />
                ) : null}
              </div>
            </div>
          </div>

          <div style={{ position: "absolute", inset: 0, opacity: overtime, paddingTop: 8 }}>
            <RateRow label="時間外" rate="二割五分" fill={overA * 0.42} />
            <div style={{ textAlign: "center", color: GOLD, fontSize: 34, lineHeight: 1, height: 32 }}>+</div>
            <div style={{ transform: `translateY(${(1 - rise(frame, 430, 16)) * 10}px)` }}>
              <RateRow label="深夜" rate="二割五分" fill={overB * 0.42} />
            </div>
            <div style={{ marginTop: 18, height: 3, backgroundColor: NAVY, opacity: overSum }} />
            <div style={{ marginTop: 16, textAlign: "center", fontSize: 72, lineHeight: 1.2, opacity: overSum, transform: `translateY(${floatY}px)` }}>
              五割以上
            </div>
          </div>

          <div style={{ position: "absolute", inset: 0, opacity: holiday, paddingTop: 8 }}>
            <RateRow label="休日" rate="三割五分" fill={holiA * 0.64} />
            <div style={{ textAlign: "center", color: GOLD, fontSize: 34, lineHeight: 1, height: 32 }}>+</div>
            <RateRow label="深夜" rate="二割五分" fill={holiB * 0.46} />
            <div style={{ marginTop: 18, height: 3, backgroundColor: NAVY, opacity: holiSum }} />
            <div style={{ marginTop: 16, textAlign: "center", fontSize: 72, lineHeight: 1.2, opacity: holiSum, transform: `translateY(${floatY}px)` }}>
              六割以上
            </div>
          </div>

          <div style={{ position: "absolute", inset: 0, opacity: region, paddingTop: 24 }}>
            <div style={{ textAlign: "center", fontSize: 64, lineHeight: 1.2, transform: `translateY(${floatY}px)` }}>定める地域</div>
            <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 26, marginTop: 52 }}>
              <div style={{ textAlign: "center", opacity: 0.78 }}>
                <div style={{ fontSize: 32, lineHeight: 1.2 }}>原則</div>
                <div style={{ marginTop: 12, fontSize: 46, lineHeight: 1.15, whiteSpace: "nowrap" }}>22:00–5:00</div>
              </div>
              <div style={{ width: 64, textAlign: "center", color: GOLD, fontSize: 52, lineHeight: 1, opacity: arrow }}>→</div>
              <div style={{ textAlign: "center" }}>
                <div style={{ fontSize: 32, lineHeight: 1.2 }}>期間</div>
                <div style={{ marginTop: 12, fontSize: 46, lineHeight: 1.15, whiteSpace: "nowrap" }}>23:00–6:00</div>
              </div>
            </div>
          </div>
        </div>

        <div
          style={{
            position: "absolute",
            left: "50%",
            bottom: 64,
            width: 340,
            height: 26,
            transform: `translateX(-50%) translateX(${Math.sin(frame / 25) * 8}px)`,
            backgroundColor: "rgba(16,24,40,0.12)",
            borderRadius: "50%",
            filter: "blur(6px)",
          }}
        />
        <div
          style={{
            position: "absolute",
            left: "50%",
            bottom: 52,
            width: 460,
            height: 460,
            transform: `translateX(-50%) translateY(${Math.sin(frame / 26) * 7}px)`,
          }}
        >
          <Img
            src={staticFile("ira/kane10_city.png")}
            style={{ width: 460, height: 460, objectFit: "contain" }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};
