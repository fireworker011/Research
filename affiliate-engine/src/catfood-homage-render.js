#!/usr/bin/env node
'use strict';

/**
 * キャットフード・オマージュShorts（9:16）を、台本JSONと静止画から組む。
 *
 * 借りるのは型だけ。実投稿・アフィURL埋め込み・既存32本の編集はしない。
 *
 *   node src/catfood-homage-render.js --self-test
 *   node src/catfood-homage-render.js --print-copy
 *   node src/catfood-homage-render.js --images-dir data/catfood-homage-stills --out-dir output/videos/catfood-homage
 */

const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const { promisify } = require('util');
const { ROOT, OUTPUT_DIR, readJSON } = require('./util');
const { checkContent } = require('./compliance');
const { youtubeDescription, PROFILE_CTA } = require('./youtube-cta');

const execFileAsync = promisify(execFile);

const SCRIPTS_PATH = path.join(ROOT, 'data', 'catfood-homage-scripts.json');
const FONT_CANDIDATES = [
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
  '/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc',
  '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
  '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf'
];

const FORBIDDEN = /ジュンジュン|ランラン|junjun|ranran|りんさん|絶対|必ず|治る|毛並みが(良く|よく)なった/i;

function findFont() {
  return FONT_CANDIDATES.find((f) => fs.existsSync(f)) || null;
}

function loadPack() {
  return readJSON(SCRIPTS_PATH);
}

function escapeDrawtext(text) {
  return String(text)
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/:/g, '\\:')
    .replace(/%/g, '\\%');
}

function stillPath(imagesDir, video, beat) {
  if (beat.id === 'cta') {
    const cta = path.join(imagesDir, `${video.id}_cta.png`);
    if (fs.existsSync(cta)) return cta;
    return path.join(imagesDir, `${video.id}_b3.png`);
  }
  return path.join(imagesDir, `${video.id}_${beat.id}.png`);
}

function selfTest(pack) {
  const errors = [];
  if (!pack || !Array.isArray(pack.videos) || pack.videos.length !== 3) {
    errors.push('videos は3本必須');
    return errors;
  }
  for (const v of pack.videos) {
    if (!v.id || !v.title || !v.spoken || !v.description) {
      errors.push(`${v.id || '?'}: id/title/spoken/description 不足`);
      continue;
    }
    if (!Array.isArray(v.beats) || v.beats.length !== 4) {
      errors.push(`${v.id}: beats は4（3拍+CTA）`);
    }
    const dur = (v.beats || []).reduce((s, b) => s + Number(b.dur || 0), 0);
    if (dur < 10 || dur > 15) errors.push(`${v.id}: 合計秒数 ${dur} は10-15秒に`);
    (v.beats || []).forEach((b) => {
      const overlay = String(b.overlay || '');
      if (!overlay) errors.push(`${v.id}/${b.id}: overlay 空`);
      if (b.id !== 'cta' && overlay.length > 12) {
        errors.push(`${v.id}/${b.id}: overlay が長すぎ（${overlay.length}字）`);
      }
    });
    const last = (v.beats || [])[(v.beats || []).length - 1];
    if (!last || last.overlay !== PROFILE_CTA) {
      errors.push(`${v.id}: 末尾テロップは PROFILE_CTA と一致させる`);
    }
    const blob = `${v.title}\n${v.spoken}\n${v.description}\n${(v.beats || []).map((b) => b.overlay).join('\n')}`;
    if (FORBIDDEN.test(blob)) errors.push(`${v.id}: 禁則（元アカ名／体験談捏造／断定）`);
    if (/https?:\/\//.test(blob)) errors.push(`${v.id}: URL禁止`);
    const checked = checkContent(v.description);
    if (!checked.ok) errors.push(`${v.id}: checkContent ${checked.reasons.join('; ')}`);
    let desc;
    try {
      desc = youtubeDescription(v.spoken);
    } catch (err) {
      errors.push(`${v.id}: ${err.message}`);
      continue;
    }
    if (!/#PR/.test(v.description) || !/プロフィールのリンク/.test(v.description)) {
      errors.push(`${v.id}: 説明文に #PR とプロフィール導線が必要`);
    }
    if (!desc.includes(PROFILE_CTA)) errors.push(`${v.id}: youtubeDescription がCTAを付けない`);
  }
  return errors;
}

function printCopy(pack) {
  console.log('# キャットフード・オマージュShorts 3本（プロフィールCTA）\n');
  console.log('型だけ借用。文面はオリジナル。URLは置かない。投稿は人間。\n');
  console.log(`末尾テロップ: \`${PROFILE_CTA}\`\n`);
  pack.videos.forEach((v, i) => {
    console.log(`## ${i + 1}. ${v.id}`);
    console.log('');
    console.log(`タイトル: ${v.title}`);
    console.log('');
    console.log('テロップ:');
    (v.beats || []).forEach((b) => {
      console.log(`- ${b.dur}s ${b.overlay}`);
    });
    console.log('');
    console.log('読み上げ／説明の核:');
    console.log('```');
    console.log(v.spoken);
    console.log('```');
    console.log('');
    console.log('YouTube説明文（URLなし）:');
    console.log('```');
    console.log(v.description);
    console.log('```');
    console.log('');
  });
}

async function ensureFfmpeg() {
  try {
    await execFileAsync('ffmpeg', ['-version']);
  } catch (_) {
    throw new Error('ffmpeg がありません');
  }
}

async function renderVideo(video, imagesDir, outPath, font) {
  const inputs = [];
  const filters = [];
  video.beats.forEach((beat, i) => {
    const img = stillPath(imagesDir, video, beat);
    if (!fs.existsSync(img)) {
      throw new Error(`静止画がない: ${img}`);
    }
    inputs.push('-loop', '1', '-t', String(beat.dur + 0.2), '-i', img);
    const fontsize = beat.id === 'cta' ? 44 : 72;
    const text = escapeDrawtext(beat.overlay);
    filters.push(
      `[${i}:v]scale=1080:1920:force_original_aspect_ratio=increase,` +
        `crop=1080:1920,` +
        `drawbox=x=0:y=ih-460:w=iw:h=460:color=black@0.38:t=fill,` +
        `drawtext=fontfile='${font}':text='${text}':fontcolor=white:` +
        `fontsize=${fontsize}:borderw=5:bordercolor=black:` +
        `x=(w-text_w)/2:y=h-280:` +
        `enable='gte(t,0.15)',` +
        `fade=t=in:st=0:d=0.12,fade=t=out:st=${beat.dur}:d=0.18[v${i}]`
    );
  });
  const concatIn = video.beats.map((_, i) => `[v${i}]`).join('');
  filters.push(`${concatIn}concat=n=${video.beats.length}:v=1:a=0[out]`);

  await execFileAsync('ffmpeg', [
    '-y',
    ...inputs,
    '-filter_complex',
    filters.join(';'),
    '-map',
    '[out]',
    '-c:v',
    'libx264',
    '-pix_fmt',
    'yuv420p',
    '-r',
    '30',
    '-t',
    String(video.duration_sec),
    outPath
  ]);
}

async function main() {
  const args = process.argv.slice(2);
  const pack = loadPack();

  if (args.includes('--self-test')) {
    const errors = selfTest(pack);
    if (errors.length) {
      console.error(errors.map((e) => `- ${e}`).join('\n'));
      process.exit(1);
    }
    console.log('ok: catfood homage scripts (3) passed structure + compliance');
    return;
  }

  if (args.includes('--print-copy')) {
    printCopy(pack);
    return;
  }

  const imagesIdx = args.indexOf('--images-dir');
  const outIdx = args.indexOf('--out-dir');
  const imagesDir = path.resolve(
    imagesIdx !== -1 ? args[imagesIdx + 1] : path.join(ROOT, 'data', 'catfood-homage-stills')
  );
  const outDir = path.resolve(
    outIdx !== -1 ? args[outIdx + 1] : path.join(OUTPUT_DIR, 'videos', 'catfood-homage')
  );

  const errors = selfTest(pack);
  if (errors.length) {
    console.error(errors.map((e) => `- ${e}`).join('\n'));
    process.exit(1);
  }

  await ensureFfmpeg();
  const font = findFont();
  if (!font) {
    console.error('日本語フォントがありません（fonts-wqy-microhei または fonts-noto-cjk）');
    process.exit(1);
  }

  fs.mkdirSync(outDir, { recursive: true });
  for (const video of pack.videos) {
    const outPath = path.join(outDir, `${video.id}.mp4`);
    console.log(`render ${video.id} -> ${outPath}`);
    await renderVideo(video, imagesDir, outPath, font);
  }
  console.log(`done: ${outDir}`);
  console.log('投稿しない。YouTube Studio で人間が上げる。説明欄にURLを置かない。');
}

main().catch((err) => {
  console.error(err.message || err);
  process.exit(1);
});
