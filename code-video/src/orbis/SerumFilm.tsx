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
import { mono, sans } from "../fonts";

export const SERUM_FPS = 30;
export const SERUM_WIDTH = 1080;
export const SERUM_HEIGHT = 1920;

const HOOK_FROM = 0;
const HOOK_DURATION = 90;
const PRODUCT_FROM = 90;
const PRODUCT_DURATION = 120;
const CLAIMS_FROM = 210;
const CLAIMS_DURATION = 180;
const STEPS_FROM = 390;
const STEPS_DURATION = 120;
const CTA_FROM = 510;
const CTA_DURATION = 90;
export const SERUM_DURATION = CTA_FROM + CTA_DURATION;

const ink = "#1c1c1c";
const muted = "#6e6a64";
const line = "#d9d2c8";
const accent = "#9a3d32";

const clamp = {
  extrapolateLeft: "clamp" as const,
  extrapolateRight: "clamp" as const,
};

const Stage = ({ children }: { children: ReactNode }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#f4efe8", fontFamily: sans, color: ink }}>
      <AbsoluteFill
        style={{
          backgroundImage: `url(${staticFile("paper-noise.png")})`,
          backgroundSize: "256px 256px",
          opacity: 0.35,
          mixBlendMode: "multiply",
        }}
      />
      {children}
    </AbsoluteFill>
  );
};

const AdMark = () => {
  return (
    <div
      style={{
        position: "absolute",
        top: 120,
        left: 80,
        fontFamily: mono,
        fontSize: 26,
        letterSpacing: "0.16em",
        color: accent,
      }}
    >
      広告
    </div>
  );
};

const Bottle = ({ rise }: { rise: number }) => {
  return (
    <svg
      viewBox="0 0 280 460"
      style={{ width: 280, height: 460, display: "block", transform: `translateY(${(1 - rise) * 40}px)` }}
    >
      <rect x="108" y="8" width="64" height="28" rx="6" fill="#2a2a2a" />
      <rect x="118" y="36" width="44" height="36" fill="#3a3a3a" />
      <path d="M70 78 H210 L196 120 H84 Z" fill="#e7dfd4" stroke="#2a2a2a" strokeWidth="4" />
      <rect x="64" y="120" width="152" height="300" rx="28" fill="#f7f1e8" stroke="#2a2a2a" strokeWidth="4" />
      <rect x="86" y="250" width="108" height="8" fill="#9a3d32" />
      <text
        x="140"
        y="300"
        textAnchor="middle"
        fill="#2a2a2a"
        fontFamily={sans}
        fontSize="28"
        fontWeight="700"
      >
        SERUM
      </text>
    </svg>
  );
};

export const HookScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const enter = spring({ frame, fps, config: { damping: 16, stiffness: 90 } });

  return (
    <Stage>
      <AdMark />
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          top: 620,
          fontWeight: 900,
          fontSize: 120,
          lineHeight: 1.08,
          letterSpacing: "-0.04em",
          opacity: enter,
          transform: `translateY(${interpolate(enter, [0, 1], [28, 0])}px)`,
        }}
      >
        夜、
        <br />
        これだけ。
      </div>
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          top: 980,
          fontSize: 36,
          fontWeight: 500,
          color: muted,
          opacity: interpolate(frame, [16, 32], [0, 1], clamp),
        }}
      >
        美容液を1本足す。
      </div>
    </Stage>
  );
};

export const ProductScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rise = spring({ frame: frame - 4, fps, config: { damping: 16, stiffness: 80 } });

  return (
    <Stage>
      <AdMark />
      <div style={{ position: "absolute", left: 80, top: 240, width: 280, height: 500, opacity: rise }}>
        <Bottle rise={rise} />
      </div>
      <div style={{ position: "absolute", left: 80, right: 80, top: 820 }}>
        <div style={{ fontFamily: mono, fontSize: 28, letterSpacing: "0.14em", color: accent }}>
          ORBIS
        </div>
        <div
          style={{
            marginTop: 18,
            fontWeight: 900,
            fontSize: 72,
            lineHeight: 1.15,
            letterSpacing: "-0.04em",
          }}
        >
          ザ リンクル
          <br />
          セラム
        </div>
        <div style={{ marginTop: 28, fontSize: 32, color: muted }}>医薬部外品 · 美容液</div>
      </div>
    </Stage>
  );
};

export const ClaimsScene = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <Stage>
      <AdMark />
      <div style={{ position: "absolute", left: 80, right: 80, top: 360 }}>
        {[
          { k: "01", t: "シワ改善", n: "*1" },
          { k: "02", t: "美白", n: "*2" },
        ].map((row, index) => {
          const shown = spring({
            frame: frame - index * 8,
            fps,
            config: { damping: 200, stiffness: 120 },
          });
          return (
            <div
              key={row.k}
              style={{
                display: "flex",
                alignItems: "baseline",
                gap: 24,
                marginBottom: 36,
                paddingBottom: 28,
                borderBottom: `2px solid ${line}`,
                opacity: shown,
              }}
            >
              <div style={{ fontFamily: mono, fontSize: 28, color: accent }}>{row.k}</div>
              <div style={{ fontWeight: 900, fontSize: 84, letterSpacing: "-0.04em" }}>{row.t}</div>
              <div style={{ fontSize: 28, color: muted }}>{row.n}</div>
            </div>
          );
        })}
        <div style={{ marginTop: 28, fontSize: 30, lineHeight: 1.6, color: muted }}>
          *1 有効成分ナイアシンアミド
          <br />
          *2 メラニンの生成を抑え、
          <br />
          シミ・そばかすを防ぐ
        </div>
      </div>
    </Stage>
  );
};

const steps = ["洗顔", "化粧水", "この美容液", "保湿"] as const;

export const StepsScene = () => {
  const frame = useCurrentFrame();

  return (
    <Stage>
      <AdMark />
      <div
        style={{
          position: "absolute",
          left: 80,
          right: 80,
          top: 300,
          fontWeight: 900,
          fontSize: 56,
          letterSpacing: "-0.03em",
        }}
      >
        公式の順番
      </div>
      <div style={{ position: "absolute", left: 80, right: 80, top: 440 }}>
        {steps.map((step, index) => {
          const on = interpolate(frame, [8 + index * 8, 20 + index * 8], [0.35, 1], clamp);
          return (
            <div
              key={step}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 28,
                marginBottom: 28,
                opacity: on,
              }}
            >
              <div
                style={{
                  width: 72,
                  height: 72,
                  borderRadius: 36,
                  background: index === 2 ? accent : "#efe8df",
                  color: index === 2 ? "#f7f3ec" : ink,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  fontFamily: mono,
                  fontSize: 28,
                }}
              >
                {index + 1}
              </div>
              <div style={{ fontWeight: 700, fontSize: 48 }}>{step}</div>
            </div>
          );
        })}
        <div style={{ marginTop: 36, fontSize: 32, color: muted }}>量の目安は、パール1粒。</div>
      </div>
    </Stage>
  );
};

export const CtaScene = () => {
  const frame = useCurrentFrame();
  const opacity = interpolate(frame, [4, 16], [0, 1], clamp);

  return (
    <Stage>
      <AdMark />
      <div style={{ position: "absolute", left: 80, right: 80, top: 560, opacity }}>
        <div style={{ fontWeight: 900, fontSize: 84, lineHeight: 1.15, letterSpacing: "-0.04em" }}>
          詳しくは
          <br />
          プロフィール
        </div>
        <div style={{ marginTop: 36, fontSize: 32, color: muted, lineHeight: 1.6 }}>
          オルビス ザ リンクルセラム
          <br />
          #PR
        </div>
      </div>
    </Stage>
  );
};

export const SerumFilm = () => {
  return (
    <AbsoluteFill>
      <Sequence from={HOOK_FROM} durationInFrames={HOOK_DURATION}>
        <HookScene />
      </Sequence>
      <Sequence from={PRODUCT_FROM} durationInFrames={PRODUCT_DURATION}>
        <ProductScene />
      </Sequence>
      <Sequence from={CLAIMS_FROM} durationInFrames={CLAIMS_DURATION}>
        <ClaimsScene />
      </Sequence>
      <Sequence from={STEPS_FROM} durationInFrames={STEPS_DURATION}>
        <StepsScene />
      </Sequence>
      <Sequence from={CTA_FROM} durationInFrames={CTA_DURATION}>
        <CtaScene />
      </Sequence>
    </AbsoluteFill>
  );
};
