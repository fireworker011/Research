#!/usr/bin/env node
'use strict';

/**
 * keys/CURRENT.json を JST 今日（または --date）のキーにする。
 * 銀行メタ（期間・一覧 URL）は残す。キーが無ければ何もしない（終了 0）。
 *   node src/set-current.js
 *   node src/set-current.js --date 2026-09-15
 */

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const KEYS = path.join(ROOT, 'keys');

function jstToday() {
  return new Date(Date.now() + 9 * 3600 * 1000).toISOString().slice(0, 10);
}

function bankMeta() {
  const files = fs.readdirSync(KEYS).filter((f) => /^\d{4}-\d{2}-\d{2}\.json$/.test(f)).sort();
  const account = JSON.parse(fs.readFileSync(path.join(ROOT, 'config', 'account.json'), 'utf8'));
  const first = files[0].replace(/\.json$/, '');
  const last = files[files.length - 1].replace(/\.json$/, '');
  return {
    bank_from: first,
    bank_to: last,
    bank_days: files.length,
    bank_index: `${account.raw_base}/keys/INDEX.md`,
    key_url_pattern: `${account.raw_base}/keys/<YYYY-MM-DD>.md`
  };
}

function main() {
  const i = process.argv.indexOf('--date');
  const date = i >= 0 ? process.argv[i + 1] : jstToday();
  if (!/^\d{4}-\d{2}-\d{2}$/.test(date)) {
    console.error(`bad date ${date}`);
    process.exit(2);
  }
  const src = path.join(KEYS, `${date}.json`);
  if (!fs.existsSync(src)) {
    console.log(`no key ${date}`);
    return;
  }
  const key = JSON.parse(fs.readFileSync(src, 'utf8'));
  const next = `${JSON.stringify({ ...key, ...bankMeta() }, null, 2)}\n`;
  const dest = path.join(KEYS, 'CURRENT.json');
  const prev = fs.existsSync(dest) ? fs.readFileSync(dest, 'utf8') : '';
  if (prev === next) {
    console.log(`CURRENT.json already ${date}`);
    return;
  }
  fs.writeFileSync(dest, next);
  console.log(`CURRENT.json → ${date}`);
}

try { main(); } catch (err) {
  console.error(err.message);
  process.exit(2);
}
