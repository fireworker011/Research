'use strict';

/**
 * Instagram API with Instagram Login — Reels 投稿
 *
 * Threads と同じ Meta 系の3ステップ: ①コンテナ作成 → ②処理完了待ち → ③公開。
 * 認証: 長期ユーザートークン（60日）。refresh_access_token で延命（--refresh-tokens）。
 * スコープ: instagram_business_basic, instagram_business_content_publish
 * 制約:
 * - 動画はファイル送信不可。Meta が取りに来られる公開 https URL（video_url）が必要。
 *   item.video_url が無ければ account.public_base_url + ファイル名で組み立てる
 * - プロ（ビジネス/クリエイター）アカウントのみ。個人アカウントは API 投稿不可
 * - キャプションの URL はクリック不可。押せる場所はプロフィール
 */

const { collectEnv, fetchJSON, publicVideoUrl, sleep } = require('./common');

const API_VERSION = process.env.IG_API_VERSION || 'v26.0';
const GRAPH = `https://graph.instagram.com/${API_VERSION}`;
const REFRESH_URL = 'https://graph.instagram.com/refresh_access_token';

const LIMITS = { titleMax: 0, captionMax: 2200, hashtagMax: 30 };
const STATUS_POLL_MS = 10000;
const STATUS_POLL_MAX = 30;

function credentials(account) {
  return collectEnv({
    user_id: account.user_id_env,
    access_token: account.token_env
  });
}

async function graphPost(path, params, label) {
  const url = new URL(`${GRAPH}${path}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const { data } = await fetchJSON(url, { method: 'POST' }, label);
  return data;
}

async function graphGet(path, params, label) {
  const url = new URL(`${GRAPH}${path}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));
  const { data } = await fetchJSON(url, { method: 'GET' }, label);
  return data;
}

async function publish(account, creds, item, caption, log = () => {}) {
  const videoUrl = publicVideoUrl(item, account);
  if (!videoUrl) {
    const err = new Error('Instagram は公開 https の video_url が必要（item.video_url か account.public_base_url）');
    err.code = 'no_public_url';
    throw err;
  }

  const container = await graphPost(
    `/${creds.user_id}/media`,
    {
      media_type: 'REELS',
      video_url: videoUrl,
      caption: caption.body,
      share_to_feed: 'true',
      access_token: creds.access_token
    },
    'Instagram media'
  );
  if (!container.id) throw new Error('Instagram media: container id が返らない');

  let status = 'IN_PROGRESS';
  for (let i = 0; i < STATUS_POLL_MAX; i++) {
    await sleep(STATUS_POLL_MS);
    const st = await graphGet(`/${container.id}`, { fields: 'status_code,status', access_token: creds.access_token }, 'Instagram status');
    status = st.status_code || status;
    if (status === 'FINISHED') break;
    if (status === 'ERROR' || status === 'EXPIRED') {
      throw new Error(`Instagram container ${status}: ${st.status || ''}`);
    }
  }
  if (status !== 'FINISHED') {
    throw new Error(`Instagram container が ${STATUS_POLL_MAX * STATUS_POLL_MS / 1000}秒で FINISHED にならない（${status}）`);
  }

  const published = await graphPost(
    `/${creds.user_id}/media_publish`,
    { creation_id: container.id, access_token: creds.access_token },
    'Instagram publish'
  );
  if (!published.id) throw new Error('Instagram publish: media id が返らない');

  let permalink = null;
  try {
    const media = await graphGet(`/${published.id}`, { fields: 'permalink', access_token: creds.access_token }, 'Instagram permalink');
    permalink = media.permalink || null;
  } catch (err) {
    log(`Instagram: permalink 取得失敗（投稿は成功）: ${err.message}`);
  }
  return { id: published.id, url: permalink, video_url: videoUrl };
}

/** 長期トークンの延命（発行から24時間以上経過が条件。60日以内に1回でよい） */
async function refreshTokens(account, creds) {
  const url = new URL(REFRESH_URL);
  url.searchParams.set('grant_type', 'ig_refresh_token');
  url.searchParams.set('access_token', creds.access_token);
  const { data } = await fetchJSON(url, { method: 'GET' }, 'Instagram refresh');
  if (!data.access_token) throw new Error('Instagram refresh: access_token が返らない');
  const days = Math.round(Number(data.expires_in || 5184000) / 86400);
  return {
    updates: [{ env: account.token_env, value: data.access_token }],
    note: `次回期限 約${days}日後`
  };
}

module.exports = { platform: 'instagram', LIMITS, credentials, publish, refreshTokens };
