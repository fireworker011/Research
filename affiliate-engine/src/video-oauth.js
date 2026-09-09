#!/usr/bin/env node
'use strict';

/**
 * 手動で開設したアカウントを OAuth で登録する（ローカルで1回だけ実行）。
 *
 * アカウントの作成はしない。ブラウザでログイン済みの本人が同意画面を通し、
 * 返ってきたトークンを GitHub Secrets に入れるための値を出すだけ。
 * トークンはファイルに書かない。標準出力にだけ出す。
 *
 *   node src/video-oauth.js youtube   --account pet_youtube   --client-id ID --client-secret SECRET [--listen 8787]
 *   node src/video-oauth.js tiktok    --account pet_tiktok    --client-key KEY --client-secret SECRET --redirect-uri https://example.com/cb
 *   node src/video-oauth.js instagram --account pet_instagram --app-id ID --app-secret SECRET --redirect-uri https://example.com/cb
 *
 * --listen PORT: http://localhost:PORT/callback で code を受け取る（YouTube はこれが楽。各コンソールに同じ URI を登録する）
 * --listen なし : ブラウザのリダイレクト先 URL（または code）をターミナルに貼る。https しか登録できない TikTok / Instagram 向け
 *
 * 事前準備（各1回・人間）:
 * - YouTube: Google Cloud で YouTube Data API v3 を有効化 → OAuth クライアント（デスクトップ or Web）。
 *   同意画面を「本番」にしないと refresh_token が7日で失効する
 * - TikTok: TikTok for Developers でアプリ作成 → Login Kit + Content Posting API → scope video.publish。
 *   審査前は投稿が本人のみ公開（SELF_ONLY）
 * - Instagram: Meta for Developers でアプリ作成 → 「Instagram API with Instagram Login」→ プロアカウントで同意。
 *   scope instagram_business_basic, instagram_business_content_publish
 */

const http = require('http');
const readline = require('readline');
const crypto = require('crypto');
const { loadConfig } = require('./util');
const { fetchJSON } = require('./video-platforms/common');

const argv = process.argv.slice(2);
const platform = (argv[0] || '').toLowerCase();

function arg(name, fallback = '') {
  const i = argv.indexOf(name);
  return i !== -1 && argv[i + 1] !== undefined ? argv[i + 1] : fallback;
}

function ask(question) {
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
  return new Promise((resolve) => rl.question(question, (a) => { rl.close(); resolve(a.trim()); }));
}

/** リダイレクト先 URL か code そのものから code を取り出す */
function extractCode(input) {
  const s = String(input || '').trim();
  if (!s) return '';
  try {
    const u = new URL(s);
    return (u.searchParams.get('code') || '').replace(/#_$/, '');
  } catch (_) {
    return s.replace(/#_$/, '');
  }
}

function waitForCallback(port, expectedState) {
  return new Promise((resolve, reject) => {
    const server = http.createServer((req, res) => {
      const u = new URL(req.url, `http://localhost:${port}`);
      if (u.pathname !== '/callback') {
        res.writeHead(404).end();
        return;
      }
      const code = u.searchParams.get('code');
      const state = u.searchParams.get('state');
      const error = u.searchParams.get('error') || u.searchParams.get('error_description');
      res.writeHead(200, { 'content-type': 'text/plain; charset=utf-8' });
      if (error || !code) {
        res.end(`失敗: ${error || 'code なし'}。ターミナルに戻ってください`);
        server.close();
        reject(new Error(error || 'code が返らない'));
        return;
      }
      if (expectedState && state !== expectedState) {
        res.end('state 不一致。やり直してください');
        server.close();
        reject(new Error('state 不一致'));
        return;
      }
      res.end('登録できました。このタブは閉じてターミナルに戻ってください');
      server.close();
      resolve(code);
    });
    server.listen(port, () => console.log(`   http://localhost:${port}/callback で待機中…`));
    server.on('error', reject);
  });
}

async function obtainCode(authUrl, redirectUri, listenPort, state) {
  console.log('\n1) このURLをブラウザで開き、投稿に使うアカウントでログインして許可する:\n');
  console.log(authUrl);
  console.log('');
  if (listenPort) {
    return waitForCallback(listenPort, state);
  }
  console.log(`2) 許可後にブラウザが ${redirectUri} へ移動する。そのアドレスバーの URL 全体（または code）を貼る:`);
  const pasted = await ask('> ');
  const code = extractCode(pasted);
  if (!code) throw new Error('code を取り出せなかった');
  return code;
}

function formPost(url, params, label) {
  return fetchJSON(
    url,
    {
      method: 'POST',
      headers: { 'content-type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams(params)
    },
    label
  );
}

function accountEnvNames(accountKey) {
  const config = loadConfig('video_accounts', { accounts: [] }) || { accounts: [] };
  return (config.accounts || []).find((a) => a.key === accountKey) || null;
}

function printSecrets(pairs) {
  console.log('\n3) GitHub → Settings → Secrets and variables → Actions に、次の名前と値を登録する:\n');
  for (const [name, value] of pairs) {
    console.log(`${name}=${value}`);
  }
  console.log('\nこの出力はどこにも保存されていない。閉じる前に登録すること。ファイルやチャットに貼らない。');
}

async function youtube() {
  const acc = accountEnvNames(arg('--account')) || {};
  const clientId = arg('--client-id') || process.env.YT_CLIENT_ID;
  const clientSecret = arg('--client-secret') || process.env.YT_CLIENT_SECRET;
  if (!clientId || !clientSecret) throw new Error('--client-id と --client-secret が必要');
  const listen = parseInt(arg('--listen', '0'), 10);
  const redirectUri = arg('--redirect-uri') || (listen ? `http://localhost:${listen}/callback` : 'http://localhost:8787/callback');
  const state = crypto.randomBytes(8).toString('hex');

  const authUrl = new URL('https://accounts.google.com/o/oauth2/v2/auth');
  authUrl.search = new URLSearchParams({
    client_id: clientId,
    redirect_uri: redirectUri,
    response_type: 'code',
    scope: 'https://www.googleapis.com/auth/youtube.upload',
    access_type: 'offline',
    prompt: 'consent',
    state
  }).toString();

  const code = await obtainCode(authUrl.toString(), redirectUri, listen, state);
  const { data } = await formPost(
    'https://oauth2.googleapis.com/token',
    { code, client_id: clientId, client_secret: clientSecret, redirect_uri: redirectUri, grant_type: 'authorization_code' },
    'Google token'
  );
  if (!data.refresh_token) {
    throw new Error('refresh_token が返らない。同意画面で prompt=consent が効いているか、以前の許可を https://myaccount.google.com/permissions で取り消して再実行');
  }
  printSecrets([
    [acc.client_id_env || 'YT_<KEY>_CLIENT_ID', clientId],
    [acc.client_secret_env || 'YT_<KEY>_CLIENT_SECRET', clientSecret],
    [acc.refresh_token_env || 'YT_<KEY>_REFRESH_TOKEN', data.refresh_token]
  ]);
}

async function tiktok() {
  const acc = accountEnvNames(arg('--account')) || {};
  const clientKey = arg('--client-key') || process.env.TT_CLIENT_KEY;
  const clientSecret = arg('--client-secret') || process.env.TT_CLIENT_SECRET;
  const redirectUri = arg('--redirect-uri');
  if (!clientKey || !clientSecret || !redirectUri) throw new Error('--client-key / --client-secret / --redirect-uri（アプリに登録した https URL）が必要');
  const listen = parseInt(arg('--listen', '0'), 10);
  const state = crypto.randomBytes(8).toString('hex');

  const authUrl = new URL('https://www.tiktok.com/v2/auth/authorize/');
  authUrl.search = new URLSearchParams({
    client_key: clientKey,
    scope: 'user.info.basic,video.publish',
    response_type: 'code',
    redirect_uri: redirectUri,
    state
  }).toString();

  const code = await obtainCode(authUrl.toString(), redirectUri, listen, state);
  const { data } = await formPost(
    'https://open.tiktokapis.com/v2/oauth/token/',
    { client_key: clientKey, client_secret: clientSecret, code, grant_type: 'authorization_code', redirect_uri: redirectUri },
    'TikTok token'
  );
  if (!data.refresh_token) throw new Error(`refresh_token が返らない: ${data.error_description || data.error || JSON.stringify(data)}`);
  console.log(`\n   open_id: ${data.open_id || '-'} / scope: ${data.scope || '-'} / refresh 有効 約${Math.round((data.refresh_expires_in || 0) / 86400)}日`);
  printSecrets([
    [acc.client_key_env || 'TT_<KEY>_CLIENT_KEY', clientKey],
    [acc.client_secret_env || 'TT_<KEY>_CLIENT_SECRET', clientSecret],
    [acc.refresh_token_env || 'TT_<KEY>_REFRESH_TOKEN', data.refresh_token]
  ]);
}

async function instagram() {
  const acc = accountEnvNames(arg('--account')) || {};
  const appId = arg('--app-id') || process.env.IG_APP_ID;
  const appSecret = arg('--app-secret') || process.env.IG_APP_SECRET;
  const redirectUri = arg('--redirect-uri');
  if (!appId || !appSecret || !redirectUri) throw new Error('--app-id / --app-secret / --redirect-uri（アプリに登録した https URL）が必要');
  const listen = parseInt(arg('--listen', '0'), 10);
  const state = crypto.randomBytes(8).toString('hex');

  const authUrl = new URL('https://www.instagram.com/oauth/authorize');
  authUrl.search = new URLSearchParams({
    client_id: appId,
    redirect_uri: redirectUri,
    scope: 'instagram_business_basic,instagram_business_content_publish',
    response_type: 'code',
    state
  }).toString();

  const code = await obtainCode(authUrl.toString(), redirectUri, listen, state);
  const { data: shortLived } = await formPost(
    'https://api.instagram.com/oauth/access_token',
    { client_id: appId, client_secret: appSecret, grant_type: 'authorization_code', redirect_uri: redirectUri, code },
    'Instagram token'
  );
  if (!shortLived.access_token) throw new Error('短期トークンが返らない');

  const exchange = new URL('https://graph.instagram.com/access_token');
  exchange.search = new URLSearchParams({
    grant_type: 'ig_exchange_token',
    client_secret: appSecret,
    access_token: shortLived.access_token
  }).toString();
  const { data: longLived } = await fetchJSON(exchange, { method: 'GET' }, 'Instagram long-lived');
  if (!longLived.access_token) throw new Error('長期トークンが返らない');

  const userId = String(shortLived.user_id || '');
  console.log(`\n   user_id: ${userId || '-'} / permissions: ${(shortLived.permissions || []).join(',') || '-'} / 有効 約${Math.round((longLived.expires_in || 0) / 86400)}日`);
  printSecrets([
    [acc.user_id_env || 'IG_<KEY>_USER_ID', userId],
    [acc.token_env || 'IG_<KEY>_ACCESS_TOKEN', longLived.access_token]
  ]);
  console.log('長期トークンは60日。affiliate_engine_video_token_refresh.yml が週次で延命する。');
}

const FLOWS = { youtube, tiktok, instagram };

async function main() {
  const flow = FLOWS[platform];
  if (!flow) {
    console.error('使い方: node src/video-oauth.js <youtube|tiktok|instagram> --account <key> ...（詳細はファイル先頭）');
    process.exit(1);
  }
  console.log(`🔑 ${platform} アカウントを OAuth で登録する（アカウント自体は事前に人間が作成済みであること）`);
  await flow();
}

module.exports = { extractCode };

if (require.main === module) {
  main().catch((err) => {
    console.error(`\n🔴 ${err.message}`);
    process.exit(1);
  });
}
