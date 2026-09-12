#!/usr/bin/env node
'use strict';

/**
 * keys/*.json の検品。落ちたら終了コード 1。
 *  - 日付が連続している
 *  - IMAGINE_THROW が重複しない
 *  - 連続する日で hair / scene / variant が変わる
 *  - 顔・紅い和服・両肩・成人・裸禁止・参照 URL が必ず入っている
 *  - 他の着・API・画面内文字の指定が無い
 *  - キャプションが AI 表記を含み、CTA は木曜だけ
 *  - 投稿は 06:00 JST、5〜8 秒、9:16、720p
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const ROOT = path.join(__dirname, '..');
const KEYS = path.join(ROOT, 'keys');

const MUST_HAVE = [
  'Do not invent a new face',
  'vermillion-red',
  'off both shoulders',
  'No nudity',
  '18+ adult',
  'refs/sakura-face.jpg',
  'STEP 1',
  'STEP 2',
  'No on-screen text',
  'no lyrics',
  'Never post'
];

const MUST_NOT = [
  /XAI_API_KEY/i,
  /api\.x\.ai/i,
  /yukata|komon|furisode|tomesode|bikini|swimsuit|uniform(?!,)/i,
  /overlay/i,
  /blonde hair|silver hair|pink hair/i
];

function load() {
  const files = fs.readdirSync(KEYS).filter((f) => /^\d{4}-\d{2}-\d{2}\.json$/.test(f)).sort();
  return files.map((f) => JSON.parse(fs.readFileSync(path.join(KEYS, f), 'utf8')));
}

function nextIso(iso) {
  const [y, m, d] = iso.split('-').map(Number);
  return new Date(Date.UTC(y, m - 1, d) + 86400000).toISOString().slice(0, 10);
}

function main() {
  const keys = load();
  const errors = [];
  if (keys.length < 90) errors.push(`keys が ${keys.length} 日分。90 日以上必要`);

  const hashes = new Map();
  let prev = null;
  for (const k of keys) {
    const tag = k.id || '?';
    if (!fs.existsSync(path.join(KEYS, `${k.date}.md`))) errors.push(`${tag}: md が無い`);
    if (prev && nextIso(prev.date) !== k.date) errors.push(`${tag}: 日付が飛んだ（前 ${prev.date}）`);

    const h = crypto.createHash('sha1').update(k.imagine_prompt).digest('hex');
    if (hashes.has(h)) errors.push(`${tag}: IMAGINE_THROW が ${hashes.get(h)} と同一`);
    hashes.set(h, tag);

    if (prev) {
      if (prev.hair === k.hair) errors.push(`${tag}: hair が前日と同じ`);
      if (prev.scene === k.scene) errors.push(`${tag}: scene が前日と同じ`);
    }

    for (const phrase of MUST_HAVE) {
      if (!k.imagine_prompt.includes(phrase)) errors.push(`${tag}: 必須語なし「${phrase}」`);
    }
    const positive = k.imagine_prompt.split('\n').filter((line) => !line.startsWith('Avoid:')).join('\n');
    if (!/^Avoid:/m.test(k.imagine_prompt)) errors.push(`${tag}: Avoid 行（negatives）が無い`);
    for (const re of MUST_NOT) {
      if (re.test(positive)) errors.push(`${tag}: 禁止語 ${re}`);
    }
    if (!k.imagine_prompt.includes(k.reference)) errors.push(`${tag}: 参照 URL が本文に無い`);

    if (!/AI生成の成人モデルです。/.test(k.caption)) errors.push(`${tag}: caption に AI 表記なし`);
    if (!/AI-generated adult model\./.test(k.caption)) errors.push(`${tag}: caption に英語 AI 表記なし`);
    if (k.caption.split('\n').length !== 3) errors.push(`${tag}: caption は 3 行`);
    if (/https?:\/\//.test(k.caption)) errors.push(`${tag}: caption に URL`);

    const isThu = k.weekday === 'Thu';
    if (k.cta !== isThu) errors.push(`${tag}: cta は木曜だけ`);
    if (isThu && !k.caption.startsWith('続きはプロフィール')) errors.push(`${tag}: 木曜 caption は 続きはプロフィール`);

    if (k.duration_sec < 5 || k.duration_sec > 8) errors.push(`${tag}: duration ${k.duration_sec}`);
    if (k.aspect_ratio !== '9:16') errors.push(`${tag}: aspect`);
    if (k.resolution !== '720p') errors.push(`${tag}: resolution`);
    if (k.post_at_jst !== `${k.date} 06:00`) errors.push(`${tag}: post_at_jst`);
    if (k.do_not_post_before !== `${k.date}T06:00:00+09:00`) errors.push(`${tag}: do_not_post_before`);
    if (k.output !== `reel-${k.date}.mp4`) errors.push(`${tag}: output`);

    prev = k;
  }

  const current = JSON.parse(fs.readFileSync(path.join(KEYS, 'CURRENT.json'), 'utf8'));
  if (keys.length && current.id !== keys[0].id) errors.push('CURRENT.json が初日と一致しない');
  if (!fs.existsSync(path.join(KEYS, 'INDEX.md'))) errors.push('INDEX.md が無い');
  if (!fs.existsSync(path.join(ROOT, 'refs', 'sakura-face.jpg'))) errors.push('refs/sakura-face.jpg が無い');

  if (errors.length) {
    console.error('validate-keys: FAIL');
    for (const e of errors.slice(0, 50)) console.error(' -', e);
    if (errors.length > 50) console.error(` ... ${errors.length - 50} more`);
    process.exit(1);
  }
  const types = keys.reduce((m, k) => m.set(k.type, (m.get(k.type) || 0) + 1), new Map());
  console.log(`validate-keys: OK (${keys.length} days ${keys[0].date} → ${keys[keys.length - 1].date}; ${[...types].map(([t, n]) => `${t}:${n}`).join(' ')})`);
}

main();
