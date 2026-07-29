#!/usr/bin/env node
// STEP5 の前段: 音声・素材・BGM のマニフェストを 1 本のタイムラインにまとめる。
// Remotion 側はこの JSON だけを読む（＝生成手段が変わっても編集側は無改造）。
import path from 'node:path';
import { AUDIO_DIR, BGM_DIR, MEDIA_DIR, PUBLIC_DIR, loadScript, readJson, writeJson } from './lib/paths.mjs';

const FPS = 30;
const WIDTH = 1080;
const HEIGHT = 1920;
const HEAD_PAD = 0.12; // シーン頭の間（音声の立ち上がり前）
const TAIL_PAD = 0.28; // シーン尻の間。長すぎる無音は作らない
const MIN_TAIL_PAD = 0.1;
const OUTRO_SECONDS = 1.2; // 最後のCTAを読み切ってから少しだけ残す
const MAX_SECONDS = 59.0; // ショート枠（60秒）に収める上限

const script = loadScript();
const voice = readJson(path.join(AUDIO_DIR, 'voice-manifest.json'));
const media = readJson(path.join(MEDIA_DIR, 'media-manifest.json'));
const bgm = readJson(path.join(BGM_DIR, 'bgm-manifest.json'));

// ナレーション尺は TTS エンジンで変わるので、間（あいだ）の方を縮めて 60 秒枠に収める。
const narrationSeconds = voice.entries.reduce((a, e) => a + e.seconds, 0);
const n = script.sentences.length;
const fixed = narrationSeconds + HEAD_PAD * n + OUTRO_SECONDS;
const tailPad = Math.max(MIN_TAIL_PAD, Math.min(TAIL_PAD, (MAX_SECONDS - fixed) / n));
if (tailPad < TAIL_PAD) {
  console.log(`  [info] 60秒枠に収めるため、シーン間の余白を ${TAIL_PAD}s → ${tailPad.toFixed(2)}s に詰めました`);
}

const scenes = script.sentences.map((scene, i) => {
  const v = voice.entries[i];
  const m = media.entries[i];
  if (!v) throw new Error(`シーン ${i} の音声がありません。npm run voice を実行してください`);
  if (!m) throw new Error(`シーン ${i} の素材がありません。npm run media を実行してください`);

  const seconds = HEAD_PAD + v.seconds + tailPad;
  return {
    index: i,
    role: scene.role,
    telop: scene.telop,
    telopStyle: scene.telop_style,
    narration: scene.narration,
    audioSrc: v.src,
    audioSeconds: v.seconds,
    audioStartFrame: Math.round(HEAD_PAD * FPS),
    durationInFrames: Math.max(FPS, Math.round(seconds * FPS)), // 最低1秒
    background: m.type === 'video'
      ? { type: 'video', src: m.src, motion: m.motion }
      : { type: 'gradient', palette: m.palette, motion: m.motion },
  };
});

const bodyFrames = scenes.reduce((a, s) => a + s.durationInFrames, 0);
const durationInFrames = bodyFrames + Math.round(OUTRO_SECONDS * FPS);

const timeline = {
  fps: FPS,
  width: WIDTH,
  height: HEIGHT,
  durationInFrames,
  durationSeconds: Number((durationInFrames / FPS).toFixed(2)),
  handle: '@your_account',
  ctaUrl: 'https://x.com/comback_nao6?s=11',
  ctaLabel: 'やり方はXで',
  caption: script.caption,
  mockAudio: voice.mock === true,
  bgm: { src: bgm.src, volume: bgm.volume, duckedVolume: bgm.duckedVolume, seconds: bgm.seconds },
  scenes,
};

writeJson(path.join(PUBLIC_DIR, 'timeline.json'), timeline);

console.log('=== タイムライン生成 ===');
console.log(`  ${WIDTH}x${HEIGHT} / ${FPS}fps`);
console.log(`  ${scenes.length} シーン / ${durationInFrames} フレーム = ${timeline.durationSeconds} 秒`);
if (timeline.durationSeconds > 60) {
  console.log('  [warn] 60秒超。余白を最小にしても収まりません。台本を削るか TTS_SPEAKING_RATE を上げてください');
  console.log(`         ナレーションだけで ${narrationSeconds.toFixed(1)} 秒あります`);
}
if (bgm.seconds < timeline.durationSeconds) {
  console.log(`  [warn] BGM (${bgm.seconds}s) が本編より短いです。npm run bgm を先に流し直してください`);
}
console.log(`  音声: ${voice.mock ? 'モック（無音）' : voice.engine}`);
console.log(`  背景: ${media.source}`);
