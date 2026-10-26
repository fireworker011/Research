export const FPS = 30;
export const WIDTH = 1080;
export const HEIGHT = 1920;

export const INTRO_FROM = 0;
export const INTRO_DURATION = 132;
export const STEPS_FROM = 132;
export const STEPS_DURATION = 198;
export const PROOF_FROM = 330;
export const PROOF_DURATION = 168;
export const END_FROM = 498;
export const END_DURATION = 132;
export const DURATION = END_FROM + END_DURATION;

export const color = {
  bg: "#090909",
  paper: "#F4EFE6",
  muted: "#9A948C",
  accent: "#FF2A1A",
  card: "#141414",
  line: "#2A2A2A",
} as const;

export const steps = [
  {
    n: "01",
    title: "構成を書く",
    body: "画面の文字と順番をコードにする",
  },
  {
    n: "02",
    title: "間を決める",
    body: "動きはフレーム番号で固定する",
  },
  {
    n: "03",
    title: "MP4にする",
    body: "同じコードなら、同じ動画になる",
  },
] as const;
