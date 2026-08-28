'use strict';

const fs = require('fs');
const path = require('path');

const ROOT = path.join(__dirname, '..');
const OUTPUT_DIR = path.join(ROOT, 'output');

/** RFC4180 準拠の CSV パーサ（引用符・改行入りフィールド対応） */
function parseCSV(text) {
  const rows = [];
  let row = [];
  let field = '';
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ',') {
      row.push(field);
      field = '';
    } else if (c === '\n') {
      row.push(field);
      if (row.some((f) => f !== '')) rows.push(row);
      row = [];
      field = '';
    } else if (c !== '\r') {
      field += c;
    }
  }
  row.push(field);
  if (row.some((f) => f !== '')) rows.push(row);

  const header = rows.shift() || [];
  return rows.map((r) => Object.fromEntries(header.map((h, i) => [h, r[i] ?? ''])));
}

function escapeCSV(value) {
  const text = String(value ?? '');
  if (/[",\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function readJSON(filePath, fallback = null) {
  try {
    return JSON.parse(fs.readFileSync(filePath, 'utf-8'));
  } catch (_) {
    return fallback;
  }
}

function writeJSON(filePath, data) {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, JSON.stringify(data, null, 2), 'utf-8');
}

/** config/xxx.json を読み、無ければ config/xxx.example.json にフォールバック */
function loadConfig(name, fallback = null) {
  const real = path.join(ROOT, 'config', `${name}.json`);
  const example = path.join(ROOT, 'config', `${name}.example.json`);
  return readJSON(real) ?? readJSON(example) ?? fallback;
}

/**
 * アフィリンクを読む。ファイルの空キーは Git に残し、実 URL は
 * GitHub Secret `AFFILIATE_LINKS_JSON`（環境変数）だけから載せる。
 * 値はログに出さない。パース失敗時はファイル側のみ使う。
 */
function loadLinks() {
  const file = loadConfig('links', {}) || {};
  const out = { ...file };
  const raw = process.env.AFFILIATE_LINKS_JSON;
  if (!raw || !String(raw).trim()) return out;
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch (_) {
    console.warn('⚠️ AFFILIATE_LINKS_JSON が JSON として読めないため、ファイル側のリンクだけを使う');
    return out;
  }
  if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
    console.warn('⚠️ AFFILIATE_LINKS_JSON がオブジェクトではないため、ファイル側のリンクだけを使う');
    return out;
  }
  for (const [key, value] of Object.entries(parsed)) {
    if (key.startsWith('_')) continue;
    if (typeof value === 'string' && value.trim()) {
      out[key] = value.trim();
    }
  }
  return out;
}

/** ログ・ドライランにアフィURLを出さない */
function redactAffiliateUrls(text) {
  return String(text || '').replace(/https?:\/\/[^\s)>\]]+/gi, '[link]');
}

/** 値が入っているリンクキー数（URL は返さない） */
function countFilledLinks(links) {
  if (!links || typeof links !== 'object') return 0;
  return Object.entries(links).filter(([k, v]) => !k.startsWith('_') && String(v || '').trim()).length;
}

/** キー名だけ（値は出さない） */
function filledLinkKeys(links) {
  if (!links || typeof links !== 'object') return [];
  return Object.entries(links)
    .filter(([k, v]) => !k.startsWith('_') && String(v || '').trim())
    .map(([k]) => k);
}

/** JST の今日の日付文字列 YYYY-MM-DD */
function todayJST(offsetDays = 0) {
  const now = new Date(Date.now() + 9 * 3600 * 1000 + offsetDays * 86400 * 1000);
  return now.toISOString().split('T')[0];
}

/** スケジュール行の date + time (JST) を epoch ms に変換 */
function scheduleEpoch(date, time) {
  return new Date(`${date}T${time}:00+09:00`).getTime();
}

module.exports = {
  ROOT,
  OUTPUT_DIR,
  parseCSV,
  escapeCSV,
  readJSON,
  writeJSON,
  loadConfig,
  loadLinks,
  countFilledLinks,
  filledLinkKeys,
  redactAffiliateUrls,
  todayJST,
  scheduleEpoch
};
