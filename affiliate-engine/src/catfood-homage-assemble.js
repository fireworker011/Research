#!/usr/bin/env node
'use strict';

/**
 * 起点クリップ（無音）をテロップ付きでつなぎ、最後にナレーションだけ載せる。
 * BGM・効果音は入れない。
 *
 *   node src/catfood-homage-assemble.js --video catfood_01_bag_sound
 */

const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const { promisify } = require('util');
const { ROOT, OUTPUT_DIR, readJSON } = require('./util');
const { PROFILE_CTA } = require('./youtube-cta');

const execFileAsync = promisify(execFile);
const SCRIPTS_PATH = path.join(ROOT, 'data', 'catfood-homage-scripts.json');
const FONT_CANDIDATES = [
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
  '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
  '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
];

function findFont() {
  return FONT_CANDIDATES.find((f) => fs.existsSync(f)) || null;
}

function escapeDrawtext(text) {
  return String(text)
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/:/g, '\\:')
    .replace(/%/g, '\\%');
}

function arg(name, fallback) {
  const i = process.argv.indexOf(`--${name}`);
  return i !== -1 ? process.argv[i + 1] : fallback;
}

async function probeDuration(file) {
  const { stdout } = await execFileAsync('ffprobe', [
    '-v',
    'error',
    '-show_entries',
    'format=duration',
    '-of',
    'default=nw=1:nk=1',
    file
  ]);
  return parseFloat(String(stdout).trim());
}

async function edgeTts(text, outPath) {
  await execFileAsync('python3', [
    '-m',
    'edge_tts',
    '--voice',
    'ja-JP-NanamiNeural',
    '--rate=-8%',
    '--text',
    text,
    '--write-media',
    outPath
  ]);
}

async function telopClip(src, overlay, font, outPath, fontsize) {
  const text = escapeDrawtext(overlay);
  await execFileAsync('ffmpeg', [
    '-y',
    '-i',
    src,
    '-an',
    '-vf',
    `scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,` +
      `drawbox=x=0:y=ih-300:w=iw:h=300:color=black@0.32:t=fill,` +
      `drawtext=fontfile='${font}':text='${text}':fontcolor=white:fontsize=${fontsize}:` +
      `borderw=5:bordercolor=black:x=(w-text_w)/2:y=h-168`,
    '-c:v',
    'libx264',
    '-pix_fmt',
    'yuv420p',
    '-r',
    '30',
    outPath
  ]);
}

async function concatSilent(clips, outPath) {
  const list = `${outPath}.txt`;
  fs.writeFileSync(list, clips.map((c) => `file '${c}'`).join('\n'));
  await execFileAsync('ffmpeg', [
    '-y',
    '-f',
    'concat',
    '-safe',
    '0',
    '-i',
    list,
    '-an',
    '-c:v',
    'libx264',
    '-pix_fmt',
    'yuv420p',
    '-r',
    '30',
    outPath
  ]);
}

async function muxNarrationAfterBeats(videoPath, audioPath, storyDur, outPath) {
  const aDur = await probeDuration(audioPath);
  const delayMs = Math.round(Math.max(0, storyDur) * 1000);
  const finalDur = storyDur + aDur + 0.25;
  const filter =
    `[0:v]tpad=stop_mode=clone:stop_duration=${(finalDur + 0.5).toFixed(3)}[v];` +
    `[1:a]adelay=${delayMs}|${delayMs},apad=pad_dur=0.2[a]`;
  await execFileAsync('ffmpeg', [
    '-y',
    '-i',
    videoPath,
    '-i',
    audioPath,
    '-filter_complex',
    filter,
    '-map',
    '[v]',
    '-map',
    '[a]',
    '-c:v',
    'libx264',
    '-pix_fmt',
    'yuv420p',
    '-c:a',
    'aac',
    '-t',
    finalDur.toFixed(3),
    outPath
  ]);
}

async function main() {
  const videoId = arg('video');
  if (!videoId) {
    console.error('usage: node src/catfood-homage-assemble.js --video catfood_01_bag_sound');
    process.exit(1);
  }
  const pack = readJSON(SCRIPTS_PATH);
  const video = (pack.videos || []).find((v) => v.id === videoId);
  if (!video) {
    console.error(`unknown video: ${videoId}`);
    process.exit(1);
  }
  const font = findFont();
  if (!font) throw new Error('日本語フォントなし');

  const clipsDir = path.resolve(arg('clips-dir', path.join(OUTPUT_DIR, 'videos', 'catfood-homage', 'clips')));
  const workDir = path.join(OUTPUT_DIR, 'videos', 'catfood-homage', 'work', videoId);
  const outDir = path.resolve(arg('out-dir', path.join(OUTPUT_DIR, 'videos', 'catfood-homage')));
  fs.mkdirSync(workDir, { recursive: true });
  fs.mkdirSync(outDir, { recursive: true });

  const visualBeats = video.beats.filter((b) => b.id !== 'cta');
  const teloped = [];
  for (const beat of visualBeats) {
    const src = path.join(clipsDir, `${video.id}_${beat.id}.mp4`);
    if (!fs.existsSync(src)) throw new Error(`clip missing: ${src}`);
    const dst = path.join(workDir, `${beat.id}_telop.mp4`);
    console.log(`telop ${beat.id}: ${beat.overlay}`);
    await telopClip(src, beat.overlay, font, dst, 72);
    teloped.push(dst);
  }

  const ctaSrc = path.join(clipsDir, `${video.id}_b3.mp4`);
  const ctaDst = path.join(workDir, `cta_telop.mp4`);
  await telopClip(ctaSrc, PROFILE_CTA, font, ctaDst, 44);
  teloped.push(ctaDst);

  const silentPath = path.join(workDir, 'silent.mp4');
  await concatSilent(teloped, silentPath);

  let storyDur = 0;
  for (const clip of teloped.slice(0, -1)) {
    storyDur += await probeDuration(clip);
  }

  const narrPath = path.join(workDir, 'narration.mp3');
  const spoken = `${video.spoken} ${PROFILE_CTA}`;
  console.log('tts...');
  await edgeTts(spoken, narrPath);

  const outPath = path.join(outDir, `${video.id}_narrated.mp4`);
  await muxNarrationAfterBeats(silentPath, narrPath, storyDur, outPath);
  console.log(`done: ${outPath}`);
  console.log('音声はナレーションのみ。投稿は人間。');
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
