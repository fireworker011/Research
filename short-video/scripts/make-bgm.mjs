#!/usr/bin/env node
// STEP6: BGM。
//   外部のフリー音源はライセンス確認が要るので、ここで合成して作る（権利処理不要）。
//   落ち着いたアンビエントのコード進行 + 控えめなキック。声を邪魔しない帯域に寄せる。
//   差し替えたい場合は public/bgm/bgm.wav を好きな曲で上書きすれば動画側はそのまま動く。
import path from 'node:path';
import { BGM_DIR, AUDIO_DIR, ensureDir, readJson, writeJson } from './lib/paths.mjs';
import { writeWav } from './lib/wav.mjs';

const SR = 44100;
const BPM = 76;
const BEAT = 60 / BPM;

// Im - VI - III - VII 相当の落ち着いた進行（A マイナー）
const CHORDS = [
  [220.0, 261.63, 329.63], // Am
  [174.61, 220.0, 261.63], // F
  [196.0, 246.94, 293.66], // G
  [164.81, 196.0, 246.94], // Em
];

ensureDir(BGM_DIR);

// ナレーション尺 + 余韻ぶんだけ作る（ループの継ぎ目を作らない）
let targetSeconds = 60;
try {
  const voice = readJson(path.join(AUDIO_DIR, 'voice-manifest.json'));
  targetSeconds = voice.totalSeconds + 3;
} catch {
  console.log('[warn] voice-manifest.json が無いので 60 秒で生成します（先に npm run voice 推奨）');
}

const barSeconds = BEAT * 4;
const bars = Math.ceil(targetSeconds / barSeconds);
const totalSamples = Math.round(bars * barSeconds * SR);
const buf = new Float32Array(totalSamples);

for (let bar = 0; bar < bars; bar++) {
  const chord = CHORDS[bar % CHORDS.length];
  const start = Math.round(bar * barSeconds * SR);
  const len = Math.round(barSeconds * SR);

  // パッド: 各コード音を倍音少なめのサイン+わずかなデチューンで
  for (const freq of chord) {
    for (let n = 0; n < len; n++) {
      const t = n / SR;
      const env = Math.min(1, t / 0.6) * Math.min(1, (barSeconds - t) / 0.8); // なめらかな出入り
      const wave =
        Math.sin(2 * Math.PI * freq * t) * 0.6 +
        Math.sin(2 * Math.PI * freq * 1.003 * t) * 0.3 + // デチューンで厚み
        Math.sin(2 * Math.PI * freq * 2 * t) * 0.08;
      buf[start + n] += wave * env * 0.16;
    }
  }

  // ベース（1拍目と3拍目）: 声の帯域を避けて下に置く
  for (const beat of [0, 2]) {
    const bStart = start + Math.round(beat * BEAT * SR);
    const bLen = Math.round(BEAT * 1.6 * SR);
    const freq = chord[0] / 2;
    for (let n = 0; n < bLen && bStart + n < totalSamples; n++) {
      const t = n / SR;
      const env = Math.exp(-t * 2.2);
      buf[bStart + n] += Math.sin(2 * Math.PI * freq * t) * env * 0.18;
    }
  }

  // 拍を感じさせる程度の弱いキック
  for (let beat = 0; beat < 4; beat++) {
    const kStart = start + Math.round(beat * BEAT * SR);
    const kLen = Math.round(0.12 * SR);
    for (let n = 0; n < kLen && kStart + n < totalSamples; n++) {
      const t = n / SR;
      const env = Math.exp(-t * 26);
      const sweep = 110 * Math.exp(-t * 18) + 45; // ピッチダウン
      buf[kStart + n] += Math.sin(2 * Math.PI * sweep * t) * env * (beat % 2 === 0 ? 0.1 : 0.05);
    }
  }
}

// 全体の頭とお尻をフェード + ピーク正規化（-3dBFS）
const fade = Math.round(1.5 * SR);
for (let n = 0; n < fade; n++) {
  buf[n] *= n / fade;
  buf[totalSamples - 1 - n] *= n / fade;
}
let peak = 0;
for (const v of buf) peak = Math.max(peak, Math.abs(v));
const gain = peak > 0 ? 0.708 / peak : 1;
for (let i = 0; i < buf.length; i++) buf[i] *= gain;

const out = path.join(BGM_DIR, 'bgm.wav');
const { seconds } = writeWav(out, buf, SR);

writeJson(path.join(BGM_DIR, 'bgm-manifest.json'), {
  src: 'bgm/bgm.wav',
  seconds: Number(seconds.toFixed(3)),
  bpm: BPM,
  key: 'A minor',
  license: 'このリポジトリで合成（権利処理不要）',
  // 動画側の音量。声の明瞭さ優先で、ナレーション中はさらに下げる（ダッキング）。
  volume: 0.13,
  duckedVolume: 0.07,
  generatedAt: new Date().toISOString(),
});

console.log('=== STEP6 BGM ===');
console.log(`  ${out}`);
console.log(`  ${seconds.toFixed(1)} 秒 / ${BPM}BPM / Aマイナー / 合成音源（権利処理不要）`);
console.log(`  音量 0.13（ナレーション中は 0.07 にダッキング）`);
