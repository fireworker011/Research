#!/usr/bin/env node
'use strict';

/**
 * JST 今日の起動キーを Issue「サクラ起動キー」に書く（鏡）。
 * 本線は A が毎朝 keys/<date>.md を raw URL で読む。この Issue は起動文と今日のキーの掲示板。
 *   node src/handoff.js                 # GITHUB_TOKEN があれば Issue にコメント
 *   node src/handoff.js --local         # output/handoff-latest.md だけ
 *   node src/handoff.js --date YYYY-MM-DD
 */

const fs = require('fs');
const path = require('path');
const { execFileSync } = require('child_process');

const ROOT = path.join(__dirname, '..');
const account = JSON.parse(fs.readFileSync(path.join(ROOT, 'config', 'account.json'), 'utf8'));
const ISSUE_TITLE = account.issue_launch_key;

function jstNow() {
  return new Date(Date.now() + 9 * 3600 * 1000);
}

function jstToday() {
  return jstNow().toISOString().slice(0, 10);
}

function jstHour() {
  return jstNow().getUTCHours();
}

function argDate() {
  const i = process.argv.indexOf('--date');
  return i >= 0 ? process.argv[i + 1] : jstToday();
}

function loadBankMeta() {
  const current = JSON.parse(fs.readFileSync(path.join(ROOT, 'keys', 'CURRENT.json'), 'utf8'));
  return {
    bank_from: current.bank_from,
    bank_to: current.bank_to,
    bank_days: current.bank_days,
    bank_index: current.bank_index,
    key_url_pattern: current.key_url_pattern
  };
}

function loadKey(date) {
  const file = path.join(ROOT, 'keys', `${date}.json`);
  if (!fs.existsSync(file)) return null;
  return { ...JSON.parse(fs.readFileSync(file, 'utf8')), ...loadBankMeta() };
}

function resumeLine(hour) {
  if (hour < 5) return '05:00 JST から作成、**06:00 JST 投稿**。';
  if (hour < 6) return '**今すぐ作れ。** 06:00 JST に投稿。';
  if (hour < 8) return '**今すぐ作れ。でき次第本日分を投稿（08:00 JST まで）。**';
  return '今日は 08:00 JST 過ぎ。明日 05:00 から。';
}

function render(key, hour) {
  const base = account.raw_base;
  return [
    `<!-- sakura-today ${key.date} -->`,
    `# サクラ起動キー ${key.date}`,
    '',
    resumeLine(hour),
    '',
    `期間 **${key.bank_from} 〜 ${key.bank_to}**（${key.bank_days}日）。毎日 05:00 JST 作成、**06:00 JST 投稿**。API 不要。`,
    '',
    '## A サクラ専属自動投稿（起動文）',
    '',
    '```',
    `今日（JST）の日付で ${key.key_url_pattern} を読め。404 なら今日は何もしない。IMAGINE_THROW を B サクラImagine に参照画像2枚を添えてそのまま渡せ。文を足すな。返った mp4 を確認し、06:00 JST にキャプションそのまま投稿。05:00 を過ぎて起きて 08:00 前なら今すぐ作れ。06:00 過ぎならでき次第出せ。役割カード: ${base}/bots/A-サクラ専属自動投稿.md`,
    '```',
    '',
    '## B サクラImagine（起動文）',
    '',
    '```',
    `A から渡された IMAGINE_THROW と参照画像だけで Grok Imagine を回せ。STEP 1 で静止画、STEP 2 で動画。顔が別人なら1回だけやり直し、まだ違えば参照画像をそのまま動かせ。投稿するな。役割カード: ${base}/bots/B-サクラImagine.md`,
    '```',
    '',
    '## 場所',
    '',
    `- 今日のキー: ${base}/keys/${key.date}.md`,
    `- 一覧: ${key.bank_index}`,
    `- 参照顔: ${key.reference}`,
    `- 役割: ${base}/bots/ROSTER.md`,
    `- IG 初回設定: ${base}/ig/first-run.md`,
    '',
    `## 今日 ${key.id}（${key.weekday_ja}）`,
    '',
    `type ${key.type} / hair ${key.hair} / scene ${key.scene} / ${key.duration_sec}s / 投稿 ${key.post_at_jst} JST`,
    '',
    '```',
    key.imagine_prompt,
    '```',
    '',
    '```',
    key.caption,
    '```',
    ''
  ].join('\n');
}

function writeLocal(body) {
  const outDir = path.join(ROOT, 'output');
  fs.mkdirSync(outDir, { recursive: true });
  const file = path.join(ROOT, 'output', 'handoff-latest.md');
  fs.writeFileSync(file, body);
  return file;
}

function gh(args) {
  return execFileSync('gh', args, { encoding: 'utf8' }).trim();
}

function upsertIssue(body) {
  const raw = gh(['issue', 'list', '--search', `${ISSUE_TITLE} in:title`, '--state', 'open', '--json', 'number,title', '--limit', '20']);
  const hit = JSON.parse(raw).find((i) => i.title === ISSUE_TITLE);
  if (!hit) return { created: true, url: gh(['issue', 'create', '--title', ISSUE_TITLE, '--body', body]) };
  gh(['issue', 'comment', String(hit.number), '--body', body]);
  return { created: false, number: hit.number };
}

function main() {
  const date = argDate();
  const key = loadKey(date);
  if (!key) {
    console.log(`no key ${date}`);
    return;
  }
  const hour = process.argv.includes('--date') ? 5 : jstHour();
  const body = render(key, hour);
  console.log(`local ${writeLocal(body)}`);
  if (process.argv.includes('--local')) { console.log(`local only ${date}`); return; }
  if (!(process.env.GITHUB_TOKEN || process.env.GH_TOKEN)) { console.log('no token; local only'); return; }
  console.log(JSON.stringify(upsertIssue(body)));
}

try { main(); } catch (err) { console.error(err.message); process.exit(2); }
