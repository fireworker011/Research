#!/usr/bin/env node
'use strict';

/**
 * A の1日を模擬する（Imagine も IG も呼ばない）。
 *   node src/dry-run.js                 # 明日（JST）
 *   node src/dry-run.js --date 2026-10-01
 * raw URL からキーを取り、IMAGINE_THROW と CAPTION を切り出し、参照画像2枚が落ちるかを見る。
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const account = JSON.parse(fs.readFileSync(path.join(ROOT, 'config', 'account.json'), 'utf8'));

function tomorrowJst() {
  const now = new Date(Date.now() + 9 * 3600 * 1000 + 86400000);
  return now.toISOString().slice(0, 10);
}

function fenced(md, heading) {
  const i = md.indexOf(heading);
  if (i < 0) return null;
  const start = md.indexOf('```', i);
  const end = md.indexOf('```', start + 3);
  if (start < 0 || end < 0) return null;
  return md.slice(start + 3, end).replace(/^\n/, '').replace(/\n$/, '');
}

async function get(url) {
  const res = await fetch(url);
  return { status: res.status, buf: Buffer.from(await res.arrayBuffer()), type: res.headers.get('content-type') || '' };
}

async function main() {
  const i = process.argv.indexOf('--date');
  const date = i > 0 ? process.argv[i + 1] : tomorrowJst();
  const url = `${account.raw_base}/keys/${date}.md`;
  const fails = [];

  const key = await get(url);
  console.log(`${key.status} ${url}`);
  if (key.status === 404) { console.log('404 → A は今日は何もしない（正常）'); return; }
  if (key.status !== 200) { console.error(`key fetch ${key.status}`); process.exit(1); }
  const md = key.buf.toString('utf8');

  const throwBlock = fenced(md, '## IMAGINE_THROW');
  const caption = fenced(md, '## CAPTION');
  if (!throwBlock) fails.push('IMAGINE_THROW ブロックが切り出せない');
  if (!caption) fails.push('CAPTION ブロックが切り出せない');

  if (throwBlock) {
    for (const must of ['REFERENCE (identity, must be attached)', 'STEP 1', 'STEP 2', 'CHECK:', 'Avoid:', 'Never post']) {
      if (!throwBlock.includes(must)) fails.push(`IMAGINE_THROW に「${must}」が無い`);
    }
    if (/```/.test(throwBlock)) fails.push('IMAGINE_THROW にフェンスが混入');
  }
  if (caption) {
    if (caption.split('\n').length !== 3) fails.push('CAPTION が3行でない');
    if (!caption.includes('AI生成の成人モデルです。')) fails.push('CAPTION に AI 表記が無い');
  }

  const postAt = md.match(/投稿: \*\*(\d{4}-\d{2}-\d{2} 06:00) JST\*\*/);
  if (!postAt || !postAt[1].startsWith(date)) fails.push('投稿時刻の行が読めない');

  for (const ref of [`${account.raw_base}/refs/sakura-face.jpg`, `${account.raw_base}/refs/sakura-face-2.jpg`]) {
    const r = await get(ref);
    const jpeg = r.buf[0] === 0xff && r.buf[1] === 0xd8;
    console.log(`${r.status} ${r.buf.length}B ${jpeg ? 'jpeg' : 'NOT-JPEG'} ${ref}`);
    if (r.status !== 200 || !jpeg) fails.push(`参照が落ちない: ${ref}`);
    if (throwBlock && !throwBlock.includes(ref)) fails.push(`IMAGINE_THROW に参照 URL が無い: ${ref}`);
  }

  console.log('');
  console.log(`date ${date}  throw ${throwBlock ? throwBlock.length : 0} chars  caption ${caption ? caption.split('\n').length : 0} lines  post ${postAt ? postAt[1] : '?'} JST`);
  if (fails.length) {
    console.error('dry-run: FAIL');
    for (const f of fails) console.error(' -', f);
    process.exit(1);
  }
  console.log('dry-run: OK（A が読めて B に渡せる形）');
}

main().catch((err) => { console.error(err.message); process.exit(1); });
