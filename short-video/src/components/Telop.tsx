import React from 'react';
import { AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';
import { COLORS, FONT_FAMILY, TELOP_SPEC, TelopStyle, outlined } from '../theme';

// テロップは画面中央〜やや下。指の位置・UIバーに隠れない高さに置く。
// ％ は「幅」基準に解決されてしまうので px で持つ（1920 の約 55%）。
const TELOP_TOP = 1050;
const SIDE_PADDING = 64;
const TELOP_MAX_WIDTH = 1080 - SIDE_PADDING * 2;

export const Telop: React.FC<{ text: string; style: TelopStyle; durationInFrames: number }> = ({
  text,
  style,
  durationInFrames,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const spec = TELOP_SPEC[style];

  const pop = spring({ frame, fps, config: { damping: 200, mass: 0.5 }, durationInFrames: 12 });
  const out = interpolate(frame, [durationInFrames - 6, durationInFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

  const body = style === 'paren' ? `【${text}】` : text;

  // 日本語は全角＝ほぼ 1em 幅。文字数から 1 行に収まるサイズへ自動で縮める。
  const fontSize = Math.min(spec.fontSize, TELOP_MAX_WIDTH / [...body].length);

  return (
    <AbsoluteFill
      style={{
        justifyContent: 'flex-start',
        alignItems: 'center',
        paddingTop: TELOP_TOP,
        paddingLeft: SIDE_PADDING,
        paddingRight: SIDE_PADDING,
        opacity: out,
      }}
    >
      <div
        style={{
          transform: `translateY(${(1 - pop) * 34}px) scale(${0.94 + pop * 0.06})`,
          opacity: pop,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontFamily: FONT_FAMILY,
            fontSize,
            lineHeight: 1.28,
            whiteSpace: 'nowrap',
            fontWeight: 700,
            letterSpacing: '0.01em',
            color: spec.color,
            ...outlined(spec.strokeWidth),
          }}
        >
          {body}
        </div>

        {/* title だけ下線バーで「掴み」を強める */}
        {style === 'title' ? (
          <div
            style={{
              margin: '28px auto 0',
              height: 10,
              width: `${interpolate(pop, [0, 1], [0, 62])}%`,
              borderRadius: 999,
              background: `linear-gradient(90deg, ${COLORS.accent}, ${COLORS.accentDeep})`,
            }}
          />
        ) : null}
      </div>
    </AbsoluteFill>
  );
};
