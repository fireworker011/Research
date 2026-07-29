#!/usr/bin/env node
// STEP4: 背景素材。
//   PEXELS_API_KEY があれば portrait 向き動画を検索してDL、無ければコード生成の
//   グラデーション背景にフォールバックする。どちらでも public/media/media-manifest.json
//   の形は同じなので、キーを入れて再実行すれば実写に差し替わる。
import fs from 'node:fs';
import path from 'node:path';
import { MEDIA_DIR, ensureDir, loadScript, sceneId, writeJson } from './lib/paths.mjs';

// シーンの内容に合わせた検索語（Pexels は英語クエリの方がヒットする）
const SCENE_QUERIES = [
  'tokyo train commute morning',
  'woman writing notebook kitchen',
  'sunrise city window',
  'calendar planner desk',
  'walking stairs morning light',
  'crowd city street blur',
  'hands typing smartphone',
  'coffee cup steam desk',
  'bookshelf reading light',
  'notebook pen writing closeup',
  'city night lights vertical',
  'sunrise skyline hope',
];

// フォールバック背景のパレット（落ち着いた朝〜夜のトーン。テロップの白抜きが乗る前提で中〜暗め）
const PALETTES = [
  ['#12233f', '#2b4a7d', '#0d1626'],
  ['#1d2b3a', '#3c5a73', '#101a24'],
  ['#2a2140', '#4b3a6e', '#150f22'],
  ['#123331', '#2d5f57', '#08201e'],
  ['#31241c', '#6b4a33', '#170f0a'],
  ['#1b2430', '#425466', '#0e141b'],
  ['#232043', '#463f79', '#12101f'],
  ['#2c1c2b', '#5c3a56', '#150d14'],
  ['#14293a', '#2f5771', '#0a1620'],
  ['#1f2a1e', '#41603c', '#0f1710'],
  ['#101a2e', '#27406b', '#070c17'],
  ['#33261a', '#7a5330', '#1a120a'],
];

const MOTIONS = ['zoom-in', 'zoom-out', 'pan-left', 'pan-right'];

const script = loadScript();
ensureDir(MEDIA_DIR);

const apiKey = process.env.PEXELS_API_KEY;
console.log('=== STEP4 背景素材 ===');
console.log(`ソース : ${apiKey ? 'Pexels API' : 'コード生成グラデーション（キー未設定）'}`);
console.log('');

const usedPexelsIds = new Set();
const entries = [];

for (const [i, scene] of script.sentences.entries()) {
  const id = sceneId(i);
  const query = SCENE_QUERIES[i % SCENE_QUERIES.length];
  const fallback = {
    index: i,
    type: 'gradient',
    palette: PALETTES[i % PALETTES.length],
    motion: MOTIONS[i % MOTIONS.length],
    query,
    telop: scene.telop,
  };

  if (!apiKey) {
    entries.push(fallback);
    console.log(`  ${id}  gradient  ${fallback.palette[1]}  ${fallback.motion}`);
    continue;
  }

  try {
    const hit = await searchPexelsPortrait(query, apiKey, usedPexelsIds);
    if (!hit) throw new Error('portrait のヒットなし');

    const file = path.join(MEDIA_DIR, `scene-${id}.mp4`);
    await download(hit.fileUrl, file);
    usedPexelsIds.add(hit.id);

    entries.push({
      index: i,
      type: 'video',
      src: `media/${path.basename(file)}`,
      motion: MOTIONS[i % MOTIONS.length],
      query,
      telop: scene.telop,
      // Pexels ライセンス: 商用利用可・クレジット任意。出典は残しておく。
      credit: { source: 'Pexels', id: hit.id, photographer: hit.photographer, url: hit.pageUrl },
    });
    console.log(`  ${id}  video     Pexels#${hit.id}  by ${hit.photographer}`);
  } catch (err) {
    entries.push({ ...fallback, fallbackReason: String(err.message ?? err) });
    console.log(`  ${id}  gradient  (Pexels失敗: ${err.message ?? err})`);
  }
}

writeJson(path.join(MEDIA_DIR, 'media-manifest.json'), {
  source: apiKey ? 'pexels' : 'generated',
  license: apiKey
    ? 'Pexels License — 商用利用可 / 帰属表示は任意 / 素材そのものの再配布・販売は不可'
    : 'このリポジトリで生成（権利処理不要）',
  generatedAt: new Date().toISOString(),
  entries,
});

console.log('');
console.log(`${entries.length} シーン分を用意しました。`);
if (!apiKey) {
  console.log('実写素材にする場合: export PEXELS_API_KEY=xxx して再実行（https://www.pexels.com/api/）');
} else {
  console.log('Pexels License: 商用利用可・クレジット任意。素材の再販売・単体再配布は不可。');
}

// ---------------------------------------------------------------- Pexels

async function searchPexelsPortrait(query, key, used) {
  const url = new URL('https://api.pexels.com/videos/search');
  url.searchParams.set('query', query);
  url.searchParams.set('orientation', 'portrait');
  url.searchParams.set('size', 'medium');
  url.searchParams.set('per_page', '15');

  const res = await fetch(url, { headers: { Authorization: key } });
  if (!res.ok) throw new Error(`Pexels API ${res.status}`);
  const { videos = [] } = await res.json();

  for (const v of videos) {
    if (used.has(v.id)) continue; // シーンごとに違う絵にする
    if (v.duration < 5) continue;
    const files = (v.video_files ?? [])
      .filter((f) => f.height > f.width) // 念のため縦を再確認
      .sort((a, b) => Math.abs(a.height - 1920) - Math.abs(b.height - 1920));
    if (!files.length) continue;
    return {
      id: v.id,
      fileUrl: files[0].link,
      photographer: v.user?.name ?? 'unknown',
      pageUrl: v.url,
    };
  }
  return null;
}

async function download(url, dest) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`DL 失敗 ${res.status}`);
  fs.writeFileSync(dest, Buffer.from(await res.arrayBuffer()));
}
