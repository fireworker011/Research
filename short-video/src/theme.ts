// テロップ・配色の設定。見た目を変えたいときはまずここ。
export const FONT_FAMILY = 'ShortJP, "Noto Sans JP", "Hiragino Sans", "Yu Gothic", sans-serif';

export const COLORS = {
  text: '#ffffff',
  outline: '#0b1220',
  accent: '#ffd54a', // paren スタイルの強調色
  accentDeep: '#ff8a3d',
  cta: '#4ec3ff',
};

export type TelopStyle = 'title' | 'paren' | 'normal';

export const TELOP_SPEC: Record<TelopStyle, { fontSize: number; color: string; strokeWidth: number }> = {
  // 1080px 幅で 10〜14 文字が 1 行に収まるサイズ
  title: { fontSize: 104, color: COLORS.text, strokeWidth: 16 },
  paren: { fontSize: 90, color: COLORS.accent, strokeWidth: 14 },
  normal: { fontSize: 96, color: COLORS.text, strokeWidth: 15 },
};

// 文字を縁取りして、どんな背景でも読めるようにする（paint-order で塗りの下に縁取り）
export const outlined = (strokeWidth: number) => ({
  WebkitTextStroke: `${strokeWidth}px ${COLORS.outline}`,
  paintOrder: 'stroke fill' as const,
  textShadow: '0 8px 28px rgba(0,0,0,0.55)',
});
