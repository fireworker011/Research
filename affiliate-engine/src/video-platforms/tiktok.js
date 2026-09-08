'use strict';

/**
 * TikTok Content Posting API — Direct Post（FILE_UPLOAD）
 *
 * 認証: Login Kit の refresh_token（365日）→ 実行ごとに access_token（24時間）へ交換。
 *       refresh_token が更新されて返ったら Secrets へ書き戻す（poster の --refresh-tokens）。
 * スコープ: video.publish
 * 制約:
 * - アプリ審査前は privacy_level が SELF_ONLY（本人のみ）に制限される。creator_info の
 *   privacy_level_options に PUBLIC_TO_EVERYONE が無ければ SELF_ONLY で投稿し、ログに残す
 * - brand_content_toggle（第三者の宣伝 = アフィ）は SELF_ONLY と併用不可
 * - チャンクは 5MB〜64MB。64MB 未満は1チャンクで送る
 */

const { collectEnv, fetchJSON, loadVideoBytes, contentTypeFor, sleep } = require('./common');

const TOKEN_URL = 'https://open.tiktokapis.com/v2/oauth/token/';
const CREATOR_INFO_URL = 'https://open.tiktokapis.com/v2/post/publish/creator_info/query/';
const INIT_URL = 'https://open.tiktokapis.com/v2/post/publish/video/init/';
const STATUS_URL = 'https://open.tiktokapis.com/v2/post/publish/status/fetch/';

const LIMITS = { titleMax: 2200, captionMax: 2200, hashtagMax: 30 };
const SINGLE_CHUNK_MAX = 64 * 1024 * 1024;
const CHUNK_SIZE = 10 * 1024 * 1024;
const STATUS_POLL_MS = 5000;
const STATUS_POLL_MAX = 36;

function credentials(account) {
  return collectEnv({
    client_key: account.client_key_env,
    client_secret: account.client_secret_env,
    refresh_token: account.refresh_token_env
  });
}

async function exchange(creds) {
  const body = new URLSearchParams({
    client_key: creds.client_key,
    client_secret: creds.client_secret,
    grant_type: 'refresh_token',
    refresh_token: creds.refresh_token
  });
  const { data } = await fetchJSON(
    TOKEN_URL,
    { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body },
    'TikTok token'
  );
  if (!data.access_token) {
    throw new Error(`TikTok token: ${data.error_description || data.error || 'access_token が返らない'}`);
  }
  return data;
}

function authHeaders(token) {
  return { Authorization: `Bearer ${token}`, 'content-type': 'application/json; charset=UTF-8' };
}

async function creatorInfo(token) {
  const { data } = await fetchJSON(CREATOR_INFO_URL, { method: 'POST', headers: authHeaders(token) }, 'TikTok creator_info');
  if (data.error && data.error.code && data.error.code !== 'ok') {
    throw new Error(`TikTok creator_info: ${data.error.code} ${data.error.message || ''}`);
  }
  return data.data || {};
}

function chooseChunking(size) {
  if (size <= SINGLE_CHUNK_MAX) {
    return { chunk_size: size, total_chunk_count: 1 };
  }
  return { chunk_size: CHUNK_SIZE, total_chunk_count: Math.floor(size / CHUNK_SIZE) };
}

function resolvePrivacy(account, info) {
  const options = Array.isArray(info.privacy_level_options) ? info.privacy_level_options : [];
  const wantPublic = (account.privacy || 'public') === 'public';
  if (wantPublic && options.includes('PUBLIC_TO_EVERYONE')) return 'PUBLIC_TO_EVERYONE';
  if (options.includes('SELF_ONLY')) return 'SELF_ONLY';
  return options[0] || 'SELF_ONLY';
}

async function publish(account, creds, item, caption, log = () => {}) {
  const tokenData = await exchange(creds);
  const token = tokenData.access_token;
  const info = await creatorInfo(token);
  const privacy = resolvePrivacy(account, info);
  if (privacy !== 'PUBLIC_TO_EVERYONE') {
    log(`TikTok: privacy_level=${privacy}（アプリ未審査の間は本人のみ公開）`);
  }

  const { bytes, source } = await loadVideoBytes(item);
  const maxSec = Number(info.max_video_post_duration_sec || 0);
  const chunking = chooseChunking(bytes.length);

  const postInfo = {
    title: caption.body,
    privacy_level: privacy,
    disable_duet: false,
    disable_comment: Boolean(info.comment_disabled),
    disable_stitch: false,
    video_cover_timestamp_ms: 1000,
    // アフィリエイト = 第三者ブランドの宣伝。公開投稿のときだけ立てられる
    brand_content_toggle: privacy === 'PUBLIC_TO_EVERYONE',
    brand_organic_toggle: false
  };

  const { data: initData } = await fetchJSON(
    INIT_URL,
    {
      method: 'POST',
      headers: authHeaders(token),
      body: JSON.stringify({
        post_info: postInfo,
        source_info: { source: 'FILE_UPLOAD', video_size: bytes.length, ...chunking }
      })
    },
    'TikTok init'
  );
  if (initData.error && initData.error.code && initData.error.code !== 'ok') {
    throw new Error(`TikTok init: ${initData.error.code} ${initData.error.message || ''}`);
  }
  const publishId = initData.data?.publish_id;
  const uploadUrl = initData.data?.upload_url;
  if (!publishId || !uploadUrl) throw new Error('TikTok init: publish_id / upload_url が返らない');

  const contentType = contentTypeFor(source);
  for (let i = 0; i < chunking.total_chunk_count; i++) {
    const start = i * chunking.chunk_size;
    const last = i === chunking.total_chunk_count - 1;
    const end = last ? bytes.length : start + chunking.chunk_size;
    const part = bytes.subarray(start, end);
    const res = await fetch(uploadUrl, {
      method: 'PUT',
      headers: {
        'content-type': contentType,
        'content-length': String(part.length),
        'content-range': `bytes ${start}-${end - 1}/${bytes.length}`
      },
      body: part
    });
    if (![200, 201, 206].includes(res.status)) {
      const text = await res.text();
      throw new Error(`TikTok upload chunk ${i + 1}/${chunking.total_chunk_count} ${res.status}: ${text.slice(0, 200)}`);
    }
  }

  let status = 'PROCESSING_UPLOAD';
  let statusData = {};
  for (let i = 0; i < STATUS_POLL_MAX; i++) {
    await sleep(STATUS_POLL_MS);
    const { data } = await fetchJSON(
      STATUS_URL,
      { method: 'POST', headers: authHeaders(token), body: JSON.stringify({ publish_id: publishId }) },
      'TikTok status'
    );
    statusData = data.data || {};
    status = statusData.status || status;
    if (status === 'PUBLISH_COMPLETE') break;
    if (status === 'FAILED') {
      throw new Error(`TikTok publish FAILED: ${statusData.fail_reason || 'unknown'}`);
    }
  }

  const postIds = Array.isArray(statusData.publicaly_available_post_id) ? statusData.publicaly_available_post_id : [];
  return {
    id: postIds[0] ? String(postIds[0]) : publishId,
    url: postIds[0] ? `https://www.tiktok.com/@${String(account.handle || '').replace(/^@/, '')}/video/${postIds[0]}` : null,
    status,
    privacy,
    max_video_post_duration_sec: maxSec,
    // refresh_token が回転した場合は poster が Secrets に書き戻す
    rotated_refresh_token: tokenData.refresh_token && tokenData.refresh_token !== creds.refresh_token ? tokenData.refresh_token : null
  };
}

/** 週次延命: refresh_token を使って新しい refresh_token を受け取る */
async function refreshTokens(account, creds) {
  const data = await exchange(creds);
  const updates = [];
  if (data.refresh_token && data.refresh_token !== creds.refresh_token) {
    updates.push({ env: account.refresh_token_env, value: data.refresh_token });
  }
  const days = Math.round(Number(data.refresh_expires_in || 0) / 86400);
  return { updates, note: days ? `refresh_token 残り約${days}日` : 'refresh_token 有効' };
}

module.exports = { platform: 'tiktok', LIMITS, credentials, publish, refreshTokens, chooseChunking, resolvePrivacy };
