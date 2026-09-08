'use strict';

/**
 * 動画アダプタ共通部。fetch だけを使い、依存ライブラリは足さない。
 */

const fs = require('fs');
const path = require('path');
const { ROOT } = require('../util');

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function env(name) {
  const v = process.env[name];
  return v && v.trim() ? v.trim() : '';
}

/** env 名の配列から値を集め、欠けている名前を返す */
function collectEnv(names) {
  const values = {};
  const missing = [];
  for (const [field, envName] of Object.entries(names)) {
    if (!envName) {
      missing.push(`(${field}_env 未設定)`);
      continue;
    }
    const v = env(envName);
    if (!v) missing.push(envName);
    values[field] = v;
  }
  return { values, missing };
}

async function fetchJSON(url, init = {}, label = 'API') {
  const res = await fetch(url, init);
  const text = await res.text();
  let data = {};
  try {
    data = text ? JSON.parse(text) : {};
  } catch (_) {
    data = { raw: text.slice(0, 300) };
  }
  if (!res.ok) {
    const message =
      data.error?.message ||
      data.error?.error_user_msg ||
      data.error_description ||
      data.error?.code ||
      data.error ||
      JSON.stringify(data).slice(0, 300);
    throw new Error(`${label} ${res.status}: ${typeof message === 'string' ? message : JSON.stringify(message)}`);
  }
  return { res, data };
}

/** リポジトリ相対 or 絶対パスを解決する */
function resolveVideoPath(videoPath) {
  if (!videoPath) return null;
  if (path.isAbsolute(videoPath)) return videoPath;
  const fromRoot = path.join(ROOT, videoPath);
  if (fs.existsSync(fromRoot)) return fromRoot;
  const fromRepo = path.join(ROOT, '..', videoPath);
  if (fs.existsSync(fromRepo)) return fromRepo;
  return fromRoot;
}

/** 動画バイト列を取得する。ローカルにあればそれを、無ければ video_url からダウンロード */
async function loadVideoBytes(item) {
  const local = resolveVideoPath(item.video_path);
  if (local && fs.existsSync(local)) {
    return { bytes: fs.readFileSync(local), source: local };
  }
  if (item.video_url) {
    const res = await fetch(item.video_url);
    if (!res.ok) throw new Error(`video_url の取得に失敗 ${res.status}: ${item.video_url}`);
    return { bytes: Buffer.from(await res.arrayBuffer()), source: item.video_url };
  }
  throw new Error(`動画ファイルが無い: ${item.video_path || '(video_path 未指定)'} / video_url 未指定`);
}

/** Instagram 用: 公開 https URL を組み立てる（無ければ null） */
function publicVideoUrl(item, account) {
  if (item.video_url && /^https:\/\//.test(item.video_url)) return item.video_url;
  const base = String(account.public_base_url || '').replace(/\/+$/, '');
  if (base && item.video_path) {
    return `${base}/${path.basename(item.video_path)}`;
  }
  return null;
}

function contentTypeFor(filePathOrUrl) {
  const ext = path.extname(String(filePathOrUrl || '')).toLowerCase();
  if (ext === '.mov') return 'video/quicktime';
  if (ext === '.webm') return 'video/webm';
  return 'video/mp4';
}

module.exports = {
  sleep,
  env,
  collectEnv,
  fetchJSON,
  resolveVideoPath,
  loadVideoBytes,
  publicVideoUrl,
  contentTypeFor
};
