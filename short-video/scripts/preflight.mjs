#!/usr/bin/env node
// STEP8: 投稿前チェック。
//   書き出した mp4 と、生成に使ったマニフェストを突き合わせて機械的に見られる分を潰す。
//   「耳と目で確認する項目」は最後にチェックリストとして出す。
import fs from 'node:fs';
import path from 'node:path';
import { execFileSync } from 'node:child_process';
import { AUDIO_DIR, BGM_DIR, OUT_DIR, PUBLIC_DIR, ROOT, loadScript, readJson } from './lib/paths.mjs';

const OUTPUT = process.argv[2] ? path.resolve(process.argv[2]) : path.join(OUT_DIR, 'short.mp4');

const script = loadScript();
const timeline = readJson(path.join(PUBLIC_DIR, 'timeline.json'));
const voice = readJson(path.join(AUDIO_DIR, 'voice-manifest.json'));
const bgm = readJson(path.join(BGM_DIR, 'bgm-manifest.json'));
const pron = readJson(path.join(ROOT, 'pronunciation.json'));

const ok = [];
const warn = [];
const ng = [];

// --- 書き出しファイル ---
if (!fs.existsSync(OUTPUT)) {
  ng.push(`${path.relative(ROOT, OUTPUT)} がありません。npm run render を実行してください`);
} else {
  const mb = fs.statSync(OUTPUT).size / 1024 / 1024;
  ok.push(`ファイル: ${path.relative(ROOT, OUTPUT)} (${mb.toFixed(1)} MB)`);
  if (mb > 280) warn.push(`${mb.toFixed(0)} MB。アップロード上限に近い場合は CRF を上げて再書き出し`);

  const probe = ffprobe(OUTPUT);
  if (probe) {
    const { width, height, fps, seconds, hasAudio } = probe;
    (width === 1080 && height === 1920 ? ok : ng).push(`解像度: ${width}x${height}（期待 1080x1920）`);
    (Math.abs(fps - 30) < 0.5 ? ok : ng).push(`フレームレート: ${fps.toFixed(2)} fps（期待 30）`);
    (hasAudio ? ok : ng).push(`音声トラック: ${hasAudio ? 'あり' : 'なし'}`);
    (seconds <= 60 ? ok : warn).push(`尺: ${seconds.toFixed(1)} 秒（ショート枠 60 秒）`);
    if (Math.abs(seconds - timeline.durationSeconds) > 0.5) {
      warn.push(`mp4 (${seconds.toFixed(1)}s) と timeline (${timeline.durationSeconds}s) の尺がずれています`);
    }
  } else {
    warn.push('ffprobe が見つからず、解像度・fps を自動確認できませんでした');
  }
}

// --- ナレーションとテロップの対応 ---
const mismatched = timeline.scenes.filter(
  (s, i) => s.telop !== script.sentences[i].telop || s.narration !== script.sentences[i].narration
);
(mismatched.length === 0 ? ok : ng).push(
  mismatched.length === 0
    ? `テロップ/ナレーションの対応: ${timeline.scenes.length} シーンすべて台本と一致`
    : `台本と timeline がずれています（${mismatched.length} シーン）。npm run timeline を流し直してください`
);

// 音声より短い枠がないか = テロップが消えた後も声が続く事故の検出
for (const s of timeline.scenes) {
  const needed = s.audioStartFrame + Math.round(s.audioSeconds * timeline.fps);
  if (needed > s.durationInFrames) {
    ng.push(`シーン ${s.index}: 音声(${needed}f)がシーン枠(${s.durationInFrames}f)より長く、途中で切れます`);
  }
}

// 長い無音（黒み・間延び）の検出
for (const s of timeline.scenes) {
  const silent = (s.durationInFrames - Math.round(s.audioSeconds * timeline.fps)) / timeline.fps;
  if (silent > 1.2) warn.push(`シーン ${s.index}: 無音が ${silent.toFixed(1)} 秒。間延びして見えます`);
}

// --- CTA ---
const tail = script.sentences.slice(-2);
(tail.every((s) => s.role === 'cta') ? ok : ng).push(
  `末尾CTA: ${tail.map((s) => s.telop).join(' → ')}`
);
(script.sentences.some((s) => s.narration.includes('やり方はXで')) ? ok : warn).push(
  `CTA文言「やり方はXで」: ${script.sentences.some((s) => s.narration.includes('やり方はXで')) ? 'あり' : 'なし'}`
);

// --- 音声・BGM ---
if (voice.mock) {
  warn.push('ナレーションがモック（無音）です。このままでは投稿できません。TTSキーを設定して再生成してください');
} else {
  ok.push(`ナレーション: ${voice.engine} / ${voice.voice}`);
}
const over5 = voice.entries.filter((e) => e.overLimit);
if (over5.length) {
  warn.push(`5秒を超えるナレーション ${over5.length} 件（シーン ${over5.map((e) => e.index).join(', ')}）`);
}
(bgm.volume >= 0.1 && bgm.volume <= 0.15 ? ok : warn).push(
  `BGM音量: ${bgm.volume}（指定 0.10〜0.15 / ナレーション中は ${bgm.duckedVolume} にダッキング）`
);
(bgm.seconds >= timeline.durationSeconds ? ok : ng).push(
  `BGM尺: ${bgm.seconds}s（本編 ${timeline.durationSeconds}s）`
);

// --- 誤読の残り ---
for (const item of pron.review_required ?? []) {
  warn.push(`要確認 ${item.where}: ${item.issue}`);
}

// --- 出力 ---
console.log('=== STEP8 投稿前チェック ===\n');
for (const m of ok) console.log(`  [OK]   ${m}`);
for (const m of warn) console.log(`  [warn] ${m}`);
for (const m of ng) console.log(`  [NG]   ${m}`);

console.log('\n--- 目と耳で確認する項目 ---');
console.log('  [ ] ナレーションとテロップが合っている（ズレ・出遅れがない）');
console.log('  [ ] 誤読・不自然な読みがない（あれば pronunciation.json に追記して再生成）');
console.log('  [ ] BGM が声を邪魔していない');
console.log('  [ ] 最後まで CTA が読める');
console.log('  [ ] 収益の断定・誇大表現になっていない');

console.log('\n--- 投稿キャプション ---');
console.log(script.caption);
console.log(`\n誘導先: ${timeline.ctaUrl}`);

if (ng.length) {
  console.log(`\nNG ${ng.length} 件。投稿前に直してください。`);
  process.exit(1);
}
console.log(`\n自動チェックは通過${warn.length ? `（warn ${warn.length} 件）` : ''}。`);

// ---------------------------------------------------------------- ffprobe

function ffprobe(file) {
  for (const bin of ffprobeCandidates()) {
    try {
      const out = execFileSync(
        bin,
        ['-v', 'error', '-show_entries', 'stream=codec_type,width,height,avg_frame_rate',
         '-show_entries', 'format=duration', '-of', 'json', file],
        { encoding: 'utf8' }
      );
      const json = JSON.parse(out);
      const v = json.streams.find((s) => s.codec_type === 'video');
      const [num, den] = (v?.avg_frame_rate ?? '0/1').split('/').map(Number);
      return {
        width: v?.width ?? 0,
        height: v?.height ?? 0,
        fps: den ? num / den : 0,
        seconds: Number(json.format?.duration ?? 0),
        hasAudio: json.streams.some((s) => s.codec_type === 'audio'),
      };
    } catch {
      // 次の候補へ
    }
  }
  return null;
}

// Remotion が同梱する ffprobe も探す（システムに ffmpeg が無い環境向け）
function ffprobeCandidates() {
  const list = ['ffprobe'];
  const compositorDir = path.join(ROOT, 'node_modules', '@remotion');
  try {
    for (const pkg of fs.readdirSync(compositorDir)) {
      if (!pkg.startsWith('compositor-')) continue;
      const p = path.join(compositorDir, pkg, 'ffprobe');
      if (fs.existsSync(p)) list.push(p);
    }
  } catch {
    // node_modules が無い場合は何もしない
  }
  if (process.env.FFPROBE_PATH) list.unshift(process.env.FFPROBE_PATH);
  return list;
}
