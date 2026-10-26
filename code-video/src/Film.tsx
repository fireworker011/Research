import type { ReactNode } from "react";
import {
  AbsoluteFill,
  Sequence,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import { mono, sans } from "./fonts";
import {
  DURATION,
  END_DURATION,
  END_FROM,
  FPS,
  HEIGHT,
  INTRO_DURATION,
  INTRO_FROM,
  PROOF_DURATION,
  PROOF_FROM,
  STEPS_DURATION,
  STEPS_FROM,
  WIDTH,
  color,
  steps,
} from "./theme";

const fade = (frame: number, from: number, to: number) =>
  interpolate(frame, [from, to], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

const SceneFrame = ({ children }: { children: ReactNode }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: color.bg }}>
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(900px 720px at 88% 6%, rgba(255,42,26,0.2), transparent 62%)",
        }}
      />
      {children}
    </AbsoluteFill>
  );
};

const Chrome = () => {
  const frame = useCurrentFrame();
  const { fps, durationInFrames } = useVideoConfig();
  const seconds = Math.floor(frame / fps);
  const clock = `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
  const progress = frame / Math.max(1, durationInFrames - 1);

  return (
    <>
      <div
        style={{
          position: "absolute",
          top: 108,
          left: 96,
          right: 96,
          zIndex: 3,
          display: "flex",
          justifyContent: "space-between",
          fontFamily: mono,
          fontSize: 26,
          letterSpacing: "0.12em",
          color: color.muted,
        }}
      >
        <span>CODE → MP4</span>
        <span>{clock}</span>
      </div>
      <div
        style={{
          position: "absolute",
          left: 96,
          right: 96,
          bottom: 120,
          zIndex: 3,
          height: 4,
          background: color.line,
        }}
      >
        <div
          style={{
            width: `${progress * 100}%`,
            height: "100%",
            background: color.accent,
          }}
        />
      </div>
    </>
  );
};

const Intro = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rule = spring({
    frame: frame - 4,
    fps,
    config: { damping: 18, stiffness: 80 },
  });
  const title = spring({
    frame: frame - 12,
    fps,
    config: { damping: 16, stiffness: 90 },
  });

  return (
    <AbsoluteFill style={{ padding: "300px 96px 0" }}>
      <div
        style={{
          width: 128,
          height: 12,
          marginBottom: 44,
          background: color.accent,
          transform: `scaleX(${rule})`,
          transformOrigin: "left center",
        }}
      />
      <div
        style={{
          fontFamily: sans,
          fontWeight: 900,
          fontSize: 132,
          lineHeight: 1.02,
          letterSpacing: "-0.05em",
          color: color.paper,
          opacity: title,
          transform: `translateY(${interpolate(title, [0, 1], [32, 0])}px)`,
        }}
      >
        コードで
        <br />
        描く
      </div>
      <div
        style={{
          marginTop: 44,
          fontFamily: sans,
          fontWeight: 500,
          fontSize: 40,
          color: color.muted,
          opacity: fade(frame, 28, 46),
        }}
      >
        生成ではなく、レンダリング。
      </div>
    </AbsoluteFill>
  );
};

const Steps = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  return (
    <AbsoluteFill style={{ padding: "300px 96px 0" }}>
      <div
        style={{
          marginBottom: 56,
          fontFamily: mono,
          fontSize: 26,
          letterSpacing: "0.16em",
          color: color.accent,
        }}
      >
        3 STEPS
      </div>
      {steps.map((step, index) => {
        const progress = spring({
          frame: frame + 18 - index * 2,
          fps,
          config: { damping: 200, stiffness: 120 },
        });
        return (
          <div
            key={step.n}
            style={{
              display: "flex",
              gap: 28,
              marginBottom: 52,
              opacity: progress,
              transform: `translateY(${interpolate(progress, [0, 1], [40, 0])}px)`,
            }}
          >
            <div
              style={{
                paddingTop: 16,
                fontFamily: mono,
                fontSize: 28,
                color: color.accent,
              }}
            >
              {step.n}
            </div>
            <div>
              <div
                style={{
                  fontFamily: sans,
                  fontWeight: 900,
                  fontSize: 64,
                  letterSpacing: "-0.04em",
                  color: color.paper,
                }}
              >
                {step.title}
              </div>
              <div
                style={{
                  marginTop: 10,
                  fontFamily: sans,
                  fontWeight: 500,
                  fontSize: 32,
                  lineHeight: 1.45,
                  color: color.muted,
                }}
              >
                {step.body}
              </div>
            </div>
          </div>
        );
      })}
    </AbsoluteFill>
  );
};

const codeLines = [
  { text: "<Title", tone: "muted" },
  { text: "  text=", tone: "paper", highlight: "コードで描く" },
  { text: "/>", tone: "muted" },
] as const;

const Proof = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const play = interpolate(frame, [36, PROOF_DURATION - 22], [0, 1], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });
  const shownFrame = Math.round(play * (DURATION - 1));

  return (
    <AbsoluteFill style={{ padding: "300px 96px 0" }}>
      <div
        style={{
          fontFamily: sans,
          fontWeight: 900,
          fontSize: 72,
          letterSpacing: "-0.04em",
          color: color.paper,
        }}
      >
        文字は、ここに置く
      </div>
      <div
        style={{
          marginTop: 48,
          padding: "40px 44px 36px",
          borderRadius: 28,
          background: color.card,
          border: `1px solid ${color.line}`,
        }}
      >
        <div
          style={{
            marginBottom: 28,
            fontFamily: mono,
            fontSize: 24,
            letterSpacing: "0.08em",
            color: color.muted,
          }}
        >
          Film.tsx
        </div>
        {codeLines.map((line, index) => {
          const progress = spring({
            frame: frame + 16 - index * 2,
            fps,
            config: { damping: 200, stiffness: 140 },
          });
          return (
            <div
              key={line.text}
              style={{
                minHeight: 52,
                fontFamily: mono,
                fontSize: 36,
                lineHeight: 1.45,
                color: line.tone === "paper" ? color.paper : color.muted,
                opacity: progress,
                transform: `translateX(${interpolate(progress, [0, 1], [16, 0])}px)`,
              }}
            >
              {line.text}
              {"highlight" in line ? (
                <span style={{ fontFamily: sans, fontWeight: 900 }}>
                  {`"${line.highlight}"`}
                </span>
              ) : null}
            </div>
          );
        })}
      </div>
      <div style={{ marginTop: 48 }}>
        <div
          style={{
            height: 8,
            borderRadius: 99,
            background: color.line,
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${play * 100}%`,
              height: "100%",
              background: color.accent,
            }}
          />
        </div>
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            marginTop: 18,
            fontFamily: mono,
            fontSize: 24,
            color: color.muted,
          }}
        >
          <span>0</span>
          <span>frame {shownFrame}</span>
          <span>{DURATION - 1}</span>
        </div>
      </div>
      <div
        style={{
          marginTop: 40,
          fontFamily: sans,
          fontWeight: 500,
          fontSize: 34,
          color: color.paper,
          opacity: fade(frame, 48, 64),
        }}
      >
        文字も間も、フレームに固定する
      </div>
    </AbsoluteFill>
  );
};

const EndCard = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const title = spring({
    frame: frame + 12,
    fps,
    config: { damping: 200, stiffness: 120 },
  });

  return (
    <AbsoluteFill style={{ padding: "420px 96px 0" }}>
      <div
        style={{
          fontFamily: mono,
          fontSize: 26,
          letterSpacing: "0.18em",
          color: color.accent,
        }}
      >
        RENDER
      </div>
      <div
        style={{
          marginTop: 24,
          fontFamily: sans,
          fontWeight: 900,
          fontSize: 120,
          letterSpacing: "-0.05em",
          color: color.paper,
          opacity: title,
          transform: `translateY(${interpolate(title, [0, 1], [36, 0])}px)`,
        }}
      >
        書き出す
      </div>
      <div
        style={{
          marginTop: 40,
          fontFamily: sans,
          fontWeight: 500,
          fontSize: 44,
          color: color.muted,
        }}
      >
        {WIDTH} × {HEIGHT}
      </div>
      <div
        style={{
          marginTop: 14,
          fontFamily: mono,
          fontSize: 30,
          color: color.muted,
        }}
      >
        {FPS}fps · {DURATION / FPS}s · 9:16
      </div>
    </AbsoluteFill>
  );
};

export const Film = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: color.bg, fontFamily: sans }}>
      <Sequence from={INTRO_FROM} durationInFrames={INTRO_DURATION}>
        <SceneFrame>
          <Intro />
        </SceneFrame>
      </Sequence>
      <Sequence from={STEPS_FROM} durationInFrames={STEPS_DURATION}>
        <SceneFrame>
          <Steps />
        </SceneFrame>
      </Sequence>
      <Sequence from={PROOF_FROM} durationInFrames={PROOF_DURATION}>
        <SceneFrame>
          <Proof />
        </SceneFrame>
      </Sequence>
      <Sequence from={END_FROM} durationInFrames={END_DURATION}>
        <SceneFrame>
          <EndCard />
        </SceneFrame>
      </Sequence>
      <Chrome />
    </AbsoluteFill>
  );
};
