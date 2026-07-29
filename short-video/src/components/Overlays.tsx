import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONT_FAMILY, outlined } from '../theme';

// 画面に薄く出し続けるアカウント名
export const Watermark: React.FC<{ handle: string }> = ({ handle }) => (
  <AbsoluteFill style={{ justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 104 }}>
    <div
      style={{
        fontFamily: FONT_FAMILY,
        fontSize: 34,
        letterSpacing: '0.06em',
        color: 'rgba(255,255,255,0.42)',
        textShadow: '0 2px 10px rgba(0,0,0,0.6)',
      }}
    >
      {handle}
    </div>
  </AbsoluteFill>
);

// 残り尺がわかるバー。離脱を抑える定番の演出。
export const ProgressBar: React.FC<{ durationInFrames: number }> = ({ durationInFrames }) => {
  const frame = useCurrentFrame();
  const progress = interpolate(frame, [0, durationInFrames], [0, 1], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ justifyContent: 'flex-start' }}>
      <div style={{ height: 8, width: '100%', background: 'rgba(255,255,255,0.14)' }}>
        <div
          style={{
            height: '100%',
            width: `${progress * 100}%`,
            background: `linear-gradient(90deg, ${COLORS.accent}, ${COLORS.accentDeep})`,
          }}
        />
      </div>
    </AbsoluteFill>
  );
};

// 末尾の残り。CTA を最後まで画面に残す。
export const EndCard: React.FC<{ label: string; xHandle: string }> = ({ label, xHandle }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const pop = spring({ frame, fps, config: { damping: 200, mass: 0.6 }, durationInFrames: 14 });

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'center',
        alignItems: 'center',
        gap: 40,
        background: 'rgba(6,10,18,0.42)',
        opacity: pop,
      }}
    >
      <div
        style={{
          fontFamily: FONT_FAMILY,
          fontSize: 108,
          fontWeight: 700,
          color: COLORS.text,
          transform: `scale(${0.92 + pop * 0.08})`,
          ...outlined(16),
        }}
      >
        {label}
      </div>
      <div
        style={{
          fontFamily: FONT_FAMILY,
          fontSize: 58,
          color: COLORS.cta,
          padding: '20px 46px',
          borderRadius: 999,
          border: `4px solid ${COLORS.cta}`,
          background: 'rgba(6,10,18,0.6)',
        }}
      >
        {xHandle}
      </div>
    </AbsoluteFill>
  );
};
