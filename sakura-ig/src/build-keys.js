#!/usr/bin/env node
'use strict';

/**
 * 起動キー銀行。日付だけから決まる（巡回カーソル無し。何度作っても同じ日は同じキー）。
 *   node src/build-keys.js --from 2026-09-13 --days 100
 * 出力: keys/<date>.md, keys/<date>.json, keys/INDEX.md, keys/CURRENT.json
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const KEYS = path.join(ROOT, 'keys');

const account = JSON.parse(fs.readFileSync(path.join(ROOT, 'config', 'account.json'), 'utf8'));
const bank = JSON.parse(fs.readFileSync(path.join(ROOT, 'prompts', 'bank.json'), 'utf8'));
const lock = fs.readFileSync(path.join(ROOT, 'prompts', 'lock.txt'), 'utf8').trim();
const kimono = fs.readFileSync(path.join(ROOT, 'prompts', 'kimono.txt'), 'utf8').trim();
const negatives = fs.readFileSync(path.join(ROOT, 'prompts', 'negatives.txt'), 'utf8').trim();

const WEEKDAY_JA = ['日', '月', '火', '水', '木', '金', '土'];
const WEEKDAY_EN = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
const SEASONAL_ONLY = new Set(['maple_red', 'first_snow']);

const REF_1 = `${account.raw_base}/refs/sakura-face.jpg`;
const REF_2 = `${account.raw_base}/refs/sakura-face-2.jpg`;

function parseArgs(argv) {
  const out = { from: null, days: 100 };
  for (let i = 2; i < argv.length; i += 1) {
    if (argv[i] === '--from') out.from = argv[++i];
    else if (argv[i] === '--days') out.days = Number(argv[++i]);
  }
  if (!out.from || !/^\d{4}-\d{2}-\d{2}$/.test(out.from)) {
    throw new Error('--from YYYY-MM-DD が必要');
  }
  if (!Number.isInteger(out.days) || out.days < 1 || out.days > 400) {
    throw new Error('--days は 1〜400');
  }
  return out;
}

function utcDate(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

function isoOf(date) {
  return date.toISOString().slice(0, 10);
}

function dayNumber(date) {
  return Math.floor(date.getTime() / 86400000);
}

function typeForWeekday(weekday) {
  const hit = Object.entries(bank.types).find(([, t]) => t.weekday === weekday);
  if (!hit) throw new Error(`type for weekday ${weekday} missing`);
  return { name: hit[0], def: hit[1] };
}

function pick(list, idx) {
  return list[((idx % list.length) + list.length) % list.length];
}

function generalScenes() {
  return bank.scene.filter((s) => !SEASONAL_ONLY.has(s.id));
}

function sceneById(id) {
  const s = bank.scene.find((x) => x.id === id);
  if (!s) throw new Error(`scene ${id} missing`);
  return s;
}

/** 通常日の場面。日番号だけで決まる。 */
function generalSceneFor(d) {
  return pick(generalScenes(), d * 7);
}

/** 季節日の場面。月で決まるが、前日・翌日（通常日）と同じなら別の場面へ。すべて日付から計算。 */
function seasonSceneFor(d, month) {
  const season = bank.season_by_month[String(month)];
  const neighbours = new Set([generalSceneFor(d - 1).id, generalSceneFor(d + 1).id]);
  if (!neighbours.has(season.scene)) return { scene: sceneById(season.scene), prop: season.prop };
  const fallback = bank.scene.find((s) => !neighbours.has(s.id) && s.id !== season.scene && !SEASONAL_ONLY.has(s.id));
  return { scene: fallback, prop: season.prop };
}

/** 日付 → キー。乱数・状態なし。 */
function buildKey(iso) {
  const date = utcDate(iso);
  const d = dayNumber(date);
  const weekday = date.getUTCDay();
  const month = date.getUTCMonth() + 1;
  const { name: type, def } = typeForWeekday(weekday);

  const hair = pick(bank.hair, d * 3);
  let scene;
  let prop = null;
  if (type === 'season') {
    ({ scene, prop } = seasonSceneFor(d, month));
  } else {
    scene = generalSceneFor(d);
  }
  const variant = pick(def.variants, d);
  const captionJp = pick(def.caption_jp, d * 2 + 1);
  const captionEn = pick(def.caption_en, d * 2 + 1);
  const tag = pick(bank.tags_rotate, d);
  const cta = Boolean(def.cta);

  const motion = prop ? `${variant.motion}. Seasonal element: ${prop}` : variant.motion;

  const step1 = [
    'STEP 1 — STILL (edit from the reference image; identity lock).',
    'Start from the attached reference image of SAKURA. Keep her exact face, eyes, nose, lips, skin tone, and body. Keep the red kimono and the off-shoulder exposure exactly as described below.',
    `Change only these three things. (1) Hair: ${hair.text}. (2) Scene: ${scene.text}. (3) Framing: ${def.framing}.`,
    'Photorealistic live-action, cinematic lighting, shallow depth of field, vertical 9:16, 2K. One woman only. No text anywhere in the image.'
  ].join(' ');

  const step2 = [
    'STEP 2 — VIDEO (animate the Step 1 still).',
    `Duration ${def.duration_sec} seconds, vertical 9:16, 720p.`,
    `The first half-second is ${variant.open}. Then ${motion}. Camera: ${variant.camera}.`,
    'Her face, hair, kimono, and exposure stay identical to the still from the first frame to the last.',
    `Sound: ${scene.ambience}; no lyrics, no song title, no voice. No on-screen text. No second person. No face morph.`
  ].join(' ');

  const fallback = 'CHECK: If the Step 1 still is not clearly the same woman as the reference, regenerate Step 1 once. If it still differs, skip Step 1 and animate the reference image itself with Step 2. Never post. Return the mp4 only.';

  const imaginePrompt = [
    `REFERENCE (identity, must be attached): ${REF_1}`,
    `REFERENCE 2 (side angle, optional): ${REF_2}`,
    '',
    lock,
    '',
    kimono,
    '',
    step1,
    '',
    step2,
    '',
    fallback,
    '',
    negatives
  ].join('\n');

  const caption = [
    `${captionJp}。AI生成の成人モデルです。`,
    `${captionEn}. AI-generated adult model.`,
    `${bank.tags_base} ${tag}`
  ].join('\n');

  const id = `reel-${iso}`;
  return {
    id,
    date: iso,
    weekday: WEEKDAY_EN[weekday],
    weekday_ja: WEEKDAY_JA[weekday],
    type,
    hair: hair.id,
    scene: scene.id,
    variant: def.variants.indexOf(variant),
    cta,
    duration_sec: def.duration_sec,
    aspect_ratio: '9:16',
    resolution: '720p',
    mode: 'reference-still-then-video',
    reference: REF_1,
    reference_2: REF_2,
    create_at_jst: `${iso} ${account.create_time_jst}`,
    post_at_jst: `${iso} ${account.post_time_jst}`,
    do_not_post_before: `${iso}T${account.post_time_jst}:00+09:00`,
    output: `reel-${iso}.mp4`,
    to: 'A サクラ専属自動投稿',
    throw_to: 'B サクラImagine',
    imagine_prompt: imaginePrompt,
    caption
  };
}

function renderMd(key) {
  return [
    `# 起動キー ${key.id}（${key.weekday_ja}）`,
    '',
    `宛先: **A サクラ専属自動投稿** → **B サクラImagine**`,
    `作成: ${key.create_at_jst} JST から。投稿: **${key.post_at_jst} JST**。それより前に投稿するな。`,
    '',
    '| 項目 | 値 |',
    '|---|---|',
    `| id | ${key.id} |`,
    `| type | ${key.type} |`,
    `| hair | ${key.hair} |`,
    `| scene | ${key.scene} |`,
    `| duration | ${key.duration_sec}s |`,
    `| aspect / res | ${key.aspect_ratio} / ${key.resolution} |`,
    `| cta | ${key.cta} |`,
    `| reference | ${key.reference} |`,
    `| reference_2 | ${key.reference_2} |`,
    `| output | ${key.output} |`,
    '',
    '## IMAGINE_THROW（B にこのまま渡す。文を足すな。参照画像を添付する）',
    '',
    '```',
    key.imagine_prompt,
    '```',
    '',
    '## CAPTION（一字も変えない）',
    '',
    '```',
    key.caption,
    '```',
    '',
    '## A の手順',
    '',
    '1. 参照画像2枚を落として B に添付し、IMAGINE_THROW を渡す',
    '2. 返ってきた mp4 を `' + key.output + '` として保存。顔が別人なら B に1回だけ再生成させ、まだ違えば今日は投稿しない',
    `3. ${key.post_at_jst} JST に sakura_ai_beauty のリールとして投稿。CAPTION をそのまま貼る`,
    '4. 投稿URLと時刻を控える（週次の数字で使う）',
    ''
  ].join('\n');
}

function main() {
  const { from, days } = parseArgs(process.argv);
  fs.mkdirSync(KEYS, { recursive: true });

  const start = utcDate(from);
  const rows = [];
  let first = null;
  for (let i = 0; i < days; i += 1) {
    const iso = isoOf(new Date(start.getTime() + i * 86400000));
    const key = buildKey(iso);
    if (!first) first = key;
    fs.writeFileSync(path.join(KEYS, `${iso}.md`), renderMd(key));
    fs.writeFileSync(path.join(KEYS, `${iso}.json`), `${JSON.stringify(key, null, 2)}\n`);
    rows.push(`| ${key.date} | ${key.weekday} | ${key.type} | ${key.hair} | ${key.scene} | ${key.variant} | ${key.cta ? 'CTA' : ''} |`);
  }

  const last = isoOf(new Date(start.getTime() + (days - 1) * 86400000));
  const index = [
    '# 起動キー一覧',
    '',
    `期間: ${from} 〜 ${last}（${days}日）。日付だけで決まる。作り直しても同じ日は同じキー。`,
    '',
    `A が読む URL: \`${account.raw_base}/keys/<YYYY-MM-DD>.md\``,
    '',
    '| date | wd | type | hair | scene | v | cta |',
    '|---|---|---|---|---|---|---|',
    ...rows,
    ''
  ].join('\n');
  fs.writeFileSync(path.join(KEYS, 'INDEX.md'), index);

  const current = {
    ...first,
    bank_from: from,
    bank_to: last,
    bank_days: days,
    bank_index: `${account.raw_base}/keys/INDEX.md`,
    key_url_pattern: `${account.raw_base}/keys/<YYYY-MM-DD>.md`
  };
  fs.writeFileSync(path.join(KEYS, 'CURRENT.json'), `${JSON.stringify(current, null, 2)}\n`);

  console.log(`keys: ${days} days ${from} → ${last}`);
}

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(err.message);
    process.exit(1);
  }
}

module.exports = { buildKey, renderMd };
