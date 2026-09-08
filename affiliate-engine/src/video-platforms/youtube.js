'use strict';

/**
 * YouTube Data API v3 — Shorts アップロード（resumable upload）
 *
 * 認証: OAuth 2.0 refresh_token（video-oauth.js で人間が1回取得）→ 実行ごとに access_token へ交換。
 * スコープ: https://www.googleapis.com/auth/youtube.upload
 * 制約: Shorts の説明欄・コメントの URL はクリック不可。説明欄に URL は置かない（youtube-cta.js）。
 *       Google Cloud の OAuth 同意画面が「テスト」のままだと refresh_token が7日で失効する。「本番」にする。
 */

const { collectEnv, fetchJSON, loadVideoBytes, contentTypeFor } = require('./common');

const TOKEN_URL = 'https://oauth2.googleapis.com/token';
const UPLOAD_URL = 'https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status';

const LIMITS = { titleMax: 100, captionMax: 5000, hashtagMax: 60 };

function credentials(account) {
  return collectEnv({
    client_id: account.client_id_env,
    client_secret: account.client_secret_env,
    refresh_token: account.refresh_token_env
  });
}

async function accessToken(creds) {
  const body = new URLSearchParams({
    client_id: creds.client_id,
    client_secret: creds.client_secret,
    refresh_token: creds.refresh_token,
    grant_type: 'refresh_token'
  });
  const { data } = await fetchJSON(
    TOKEN_URL,
    { method: 'POST', headers: { 'content-type': 'application/x-www-form-urlencoded' }, body },
    'YouTube token'
  );
  if (!data.access_token) throw new Error('YouTube token: access_token が返らない');
  return data.access_token;
}

async function publish(account, creds, item, caption) {
  const token = await accessToken(creds);
  const { bytes, source } = await loadVideoBytes(item);
  const contentType = contentTypeFor(source);

  const metadata = {
    snippet: {
      title: caption.title,
      description: caption.body,
      categoryId: String(account.category_id || '15'),
      defaultLanguage: 'ja',
      defaultAudioLanguage: 'ja'
    },
    status: {
      privacyStatus: account.privacy || 'public',
      selfDeclaredMadeForKids: false
    }
  };

  const init = await fetch(UPLOAD_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      'content-type': 'application/json; charset=UTF-8',
      'X-Upload-Content-Type': contentType,
      'X-Upload-Content-Length': String(bytes.length)
    },
    body: JSON.stringify(metadata)
  });
  if (!init.ok) {
    const text = await init.text();
    throw new Error(`YouTube upload init ${init.status}: ${text.slice(0, 300)}`);
  }
  const location = init.headers.get('location');
  if (!location) throw new Error('YouTube upload init: Location ヘッダが無い');

  const { data } = await fetchJSON(
    location,
    {
      method: 'PUT',
      headers: { 'content-type': contentType, 'content-length': String(bytes.length) },
      body: bytes
    },
    'YouTube upload'
  );
  if (!data.id) throw new Error('YouTube upload: video id が返らない');
  return { id: data.id, url: `https://www.youtube.com/shorts/${data.id}` };
}

module.exports = { platform: 'youtube', LIMITS, credentials, publish };
