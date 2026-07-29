import React from 'react';
import { AbsoluteFill, OffthreadVideo, interpolate, staticFile, useCurrentFrame, useVideoConfig } from 'remotion';

export type Motion = 'zoom-in' | 'zoom-out' | 'pan-left' | 'pan-right';

export type BackgroundSpec =
  | { type: 'video'; src: string; motion: Motion }
  | { type: 'gradient'; palette: [string, string, string] | string[]; motion: Motion };

// ゆっくりした動き（ケンバーンズ）。静止画的な間延びを防ぐ。
const useMotionTransform = (motion: Motion, durationInFrames: number) => {
  const frame = useCurrentFrame();
  const p = interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: 'clamp' });

  switch (motion) {
    case 'zoom-in':
      return `scale(${1.06 + p * 0.09})`;
    case 'zoom-out':
      return `scale(${1.15 - p * 0.09})`;
    case 'pan-left':
      return `scale(1.14) translateX(${(0.5 - p) * 5}%)`;
    case 'pan-right':
      return `scale(1.14) translateX(${(p - 0.5) * 5}%)`;
  }
};

export const Background: React.FC<{ spec: BackgroundSpec; durationInFrames: number }> = ({
  spec,
  durationInFrames,
}) => {
  const transform = useMotionTransform(spec.motion, durationInFrames);

  return (
    <AbsoluteFill style={{ overflow: 'hidden', backgroundColor: '#0b1220' }}>
      <AbsoluteFill style={{ transform, willChange: 'transform' }}>
        {spec.type === 'video' ? (
          <OffthreadVideo
            src={staticFile(spec.src)}
            muted
            // 素材が本編より短いときは最後のフレームで止める（黒みを出さない）
            playbackRate={1}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }}
          />
        ) : (
          <GradientCanvas palette={spec.palette} />
        )}
      </AbsoluteFill>

      {/* テロップを読みやすくする暗幕（上下を締めて中央を少し明るく残す） */}
      <AbsoluteFill
        style={{
          background:
            'linear-gradient(180deg, rgba(6,10,18,0.58) 0%, rgba(6,10,18,0.10) 34%, rgba(6,10,18,0.22) 58%, rgba(6,10,18,0.72) 100%)',
        }}
      />
    </AbsoluteFill>
  );
};

// Pexels キーが無いときの背景。ゆっくり動く光のにじみで「単色べた塗り」に見えないようにする。
// レイヤーを重ねると 1080x1920 のソフトウェア描画では急激に遅くなるので、
// CSS の多重背景で 1 パスにまとめている（blur / mix-blend-mode も使わない）。
const GradientCanvas: React.FC<{ palette: string[] }> = ({ palette }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const t = frame / fps;
  const [base, glow, deep] = palette;

  const drift = (speed: number, amp: number, phase: number) => Math.sin(t * speed + phase) * amp;

  return (
    <AbsoluteFill
      style={{
        // 手前から奥へ: 周辺減光 → 光のにじみ2つ → ベースのグラデーション
        backgroundImage: [
          'radial-gradient(70% 55% at 50% 48%, transparent 45%, rgba(0,0,0,0.42) 100%)',
          `radial-gradient(60% 40% at ${50 + drift(0.28, 12, 0)}% ${32 + drift(0.21, 8, 1.1)}%, ${hexToRgba(glow, 0.85)} 0%, transparent 62%)`,
          `radial-gradient(52% 34% at ${34 + drift(0.19, 14, 2.4)}% ${72 + drift(0.24, 9, 0.7)}%, ${hexToRgba(glow, 0.7)} 0%, transparent 58%)`,
          `linear-gradient(160deg, ${base} 0%, ${deep} 100%)`,
        ].join(','),
      }}
    />
  );
};

const hexToRgba = (hex: string, alpha: number) => {
  const v = hex.replace('#', '');
  const n = parseInt(v.length === 3 ? v.split('').map((c) => c + c).join('') : v, 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${alpha})`;
};
