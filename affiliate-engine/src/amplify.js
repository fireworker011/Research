#!/usr/bin/env node
'use strict';

/**
 * Amplify — バズ投稿への自動リンク増幅
 *
 * 「伸びた投稿のリプ欄にリンクを置く」という Threads の定石を自動化する。
 * 本文にリンクを貼るとリーチが下がりやすい一方、バズった投稿のリプ欄は
 * その投稿を見た人だけが通る導線になる（=手数勝負でバズを収益化する装置）。
 *
 * 動作:
 * 1. 各アカウントの直近72時間の投稿のビュー数を Insights API で取得
 * 2. しきい値（AMPLIFY_MIN_VIEWS、既定500）を超えた投稿に対し、
 *    そのジャンルのアフィリンクが config/links.json に設定されていれば
 *    「まとめはこちら → リンク #PR」形式のセルフリプライを1回だけ付ける
 * 3. 二重リプ防止は output/state/posted.json の amplified で管理
 * 4. 1アカウント1日最大 AMPLIFY_MAX_PER_DAY 回（既定2。リンク連発によるスパム判定回避）
 *
 * 既定はオフ。AMPLIFY_ENABLED=1 のときだけ動く。
 * A8 FAQ は Threads 本文の広告リンクを控える。円の置き場はプロフィール欄。
 * 指令塔がリプ増幅を出すまで環境変数を足すな。cron 独断再開と一緒にオンにするな。
 */

const path = require('path');
const { checkContent } = require('./compliance');
const { OUTPUT_DIR, readJSON, writeJSON, loadConfig, loadLinks, redactAffiliateUrls, todayJST } = require('./util');
const { sleep } = require('./claude-client');

const THREADS_API = 'https://graph.threads.net/v1.0';
const MIN_VIEWS = parseInt(process.env.AMPLIFY_MIN_VIEWS || '500', 10);
const MAX_PER_DAY = parseInt(process.env.AMPLIFY_MAX_PER_DAY || '2', 10);
const LOOKBACK_HOURS = parseFloat(process.env.AMPLIFY_LOOKBACK_HOURS || '72');
const STATE_PATH = path.join(OUTPUT_DIR, 'state', 'posted.json');

const isDryRun = process.argv.includes('--dry-run');

/** ジャンル別のリプライ文（2パターンを post_id で決定論的に選ぶ） */
const REPLY_TEMPLATES = {
  婚活: [
    '読んでくれた方向けに、比較して整理した結婚相談所のまとめを置いておきます → {{LINK}}\n#PR',
    '本気で動きたい人向けに、無料で資料請求できる相談所の比較はこちら → {{LINK}}\n#PR'
  ],
  副業: [
    'この話の具体的な始め方をまとめてあります → {{LINK}}\n#PR',
    '実際に使っているサービスはここに整理しています → {{LINK}}\n#PR'
  ],
  美容: [
    '記事内で触れた最低限ケアの詳細はこちらにまとめています → {{LINK}}\n#PR',
    '私が基準にしている選び方はここに整理しました（感じ方には個人差があります） → {{LINK}}\n#PR'
  ],
  筋トレ: [
    '食事側の整え方はここにまとめています → {{LINK}}\n#PR',
    '続けるために使っているものの比較はこちら → {{LINK}}\n#PR'
  ],
  教育: [
    '検討の手順と資料請求先はここに整理しています → {{LINK}}\n#PR',
    '比較したときのメモをまとめました。参考になれば → {{LINK}}\n#PR'
  ],
  節約: [
    '固定費の見直し手順はここに全部まとめています → {{LINK}}\n#PR',
    '実際の乗り換え手順の整理はこちら → {{LINK}}\n#PR'
  ],
  転職: [
    '市場価値の確かめ方はここに整理しています → {{LINK}}\n#PR',
    '無料でできる準備のまとめはこちら → {{LINK}}\n#PR'
  ],
  ペット: [
    '比較したときのメモをここにまとめています → {{LINK}}\n#PR',
    '選び方の基準はこちらに整理しました → {{LINK}}\n#PR'
  ],
  睡眠: [
    '選び方の基準をここにまとめています（個人差があります） → {{LINK}}\n#PR',
    '比較の詳細はこちらに整理しました → {{LINK}}\n#PR'
  ]
};

async function threadsGet(endpoint, params) {
  const url = new URL(`${THREADS_API}${endpoint}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Threads API ${res.status}: ${data.error?.message || JSON.stringify(data)}`);
  return data;
}

async function threadsPost(endpoint, params) {
  const url = new URL(`${THREADS_API}${endpoint}`);
  for (const [k, v] of Object.entries(params)) url.searchParams.set(k, v);
  const res = await fetch(url, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(`Threads API ${res.status}: ${data.error?.message || JSON.stringify(data)}`);
  return data;
}

async function getViews(mediaId, token) {
  try {
    const data = await threadsGet(`/${mediaId}/insights`, { metric: 'views', access_token: token });
    const m = (data.data || [])[0] || {};
    if (m.total_value?.value != null) return m.total_value.value;
    if (Array.isArray(m.values) && m.values.length) return m.values[m.values.length - 1].value || 0;
    return 0;
  } catch (_) {
    return 0;
  }
}

const HIGH_TICKET_KEYS = {
  転職: ['転職_neo', '転職_チケット', '転職_エージェント', '転職_スカウト', '転職'],
  教育: ['教育_N高', '教育_アイズ', '教育_ヒューマン', '教育']
};

function filledLink(links, key) {
  const v = links && key ? links[key] : '';
  return typeof v === 'string' && v.trim() ? v.trim() : '';
}

/** 高単価キーを先に使う。ジャンル共通やエージェントより neo / N高 を優先する */
function resolveLink(links, genre) {
  const prefer = HIGH_TICKET_KEYS[genre];
  if (prefer) {
    for (const k of prefer) {
      const v = filledLink(links, k);
      if (v) return v;
    }
    return null;
  }
  const direct = filledLink(links, genre);
  if (direct) return direct;
  for (const [k, v] of Object.entries(links || {})) {
    if (k.startsWith('_')) continue;
    if (k === '申込_auひかり') continue;
    if (v && k.startsWith(`${genre}_`)) {
      const t = filledLink(links, k);
      if (t) return t;
    }
  }
  return null;
}

async function replyToPost(userId, token, postId, text) {
  const container = await threadsPost(`/${userId}/threads`, {
    media_type: 'TEXT',
    text,
    reply_to_id: postId,
    access_token: token
  });
  await sleep(2000);
  const published = await threadsPost(`/${userId}/threads_publish`, {
    creation_id: container.id,
    access_token: token
  });
  return published.id;
}

async function main() {
  console.log(`📈 Amplify（バズ投稿へのリンク増幅）${isDryRun ? '（ドライラン）' : ''}\n`);
  if (process.env.AMPLIFY_ENABLED !== '1') {
    console.log('⏭  AMPLIFY_ENABLED≠1 のためリプ増幅しない（Threads 本文/リプのアフィは控える。円の置き場はプロフィール）');
    return;
  }
  const accountsConfig = loadConfig('accounts', { accounts: [] });
  const links = loadLinks();
  const state = readJSON(STATE_PATH, { posted: {} });
  state.amplified = state.amplified || {};

  const today = todayJST();
  const cutoff = Date.now() - LOOKBACK_HOURS * 3600 * 1000;

  // 認知フェーズ中は何もしない
  if (accountsConfig.awareness_until && today < accountsConfig.awareness_until) {
    console.log(`🌱 認知フェーズ（〜${accountsConfig.awareness_until}）のためスキップ`);
    return;
  }

  let amplifiedCount = 0;
  for (const account of accountsConfig.accounts.filter((a) => a.enabled !== false)) {
    const userId = process.env[account.user_id_env];
    const token = process.env[account.token_env];
    if (!userId || !token) continue;

    const link = resolveLink(links, account.genre);
    if (!link) continue; // リンク未設定ジャンルは対象外

    const todayCount = Object.values(state.amplified).filter(
      (v) => v.account === account.key && v.date === today
    ).length;
    if (todayCount >= MAX_PER_DAY) continue;

    let posts;
    try {
      posts = await threadsGet(`/${userId}/threads`, {
        fields: 'id,text,timestamp,permalink',
        limit: '25',
        access_token: token
      });
    } catch (err) {
      console.log(`⚠️ ${account.key}: 投稿一覧取得失敗（${err.message}）`);
      continue;
    }

    let remaining = MAX_PER_DAY - todayCount;
    for (const post of posts.data || []) {
      if (remaining <= 0) break;
      if (state.amplified[post.id]) continue;
      if (post.timestamp && new Date(post.timestamp).getTime() < cutoff) continue;
      const postText = post.text || '';
      if (/https?:\/\//.test(postText) || postText.includes('#PR')) continue; // リンク投稿自体は対象外

      const views = await getViews(post.id, token);
      if (views < MIN_VIEWS) continue;

      const variants = REPLY_TEMPLATES[account.genre] || [`詳しくはこちらにまとめています → {{LINK}}\n#PR`];
      const idx = parseInt(String(post.id).slice(-4), 10) % variants.length;
      let replyText = variants[idx].replaceAll('{{LINK}}', link);
      const compliance = checkContent(replyText);
      if (!compliance.ok) continue;
      replyText = compliance.text;

      if (isDryRun) {
        console.log(`📝 ${account.key}: views=${views} ${post.permalink || post.id}`);
        console.log(redactAffiliateUrls(replyText).split('\n').map((l) => `   │ ${l}`).join('\n'));
        remaining--;
        continue;
      }

      try {
        const replyId = await replyToPost(userId, token, post.id, replyText);
        state.amplified[post.id] = { date: today, account: account.key, views, reply_id: replyId };
        console.log(`✅ ${account.key}: views=${views} の投稿にリンクリプライ (${replyId})`);
        amplifiedCount++;
        remaining--;
        await sleep(5000);
      } catch (err) {
        console.log(`❌ ${account.key}: リプライ失敗（${err.message}）`);
      }
    }
  }

  if (!isDryRun) {
    writeJSON(STATE_PATH, state);
  }
  console.log(`\n完了: リンク増幅 ${amplifiedCount} 件`);
}

function selfTest() {
  const both = {
    転職: 'https://example.invalid/genre',
    転職_エージェント: 'https://example.invalid/agent',
    転職_neo: 'https://example.invalid/neo'
  };
  if (resolveLink(both, '転職') !== 'https://example.invalid/neo') throw new Error('prefer neo');
  const agentOnly = { 転職: '', 転職_エージェント: 'https://example.invalid/agent', 転職_neo: '' };
  if (resolveLink(agentOnly, '転職') !== 'https://example.invalid/agent') throw new Error('agent when no neo');
  const empty = { 転職: '', 転職_neo: '' };
  if (resolveLink(empty, '転職') !== null) throw new Error('empty');
  const edu = { 教育_ヒューマン: 'https://example.invalid/human', 教育_N高: 'https://example.invalid/nko' };
  if (resolveLink(edu, '教育') !== 'https://example.invalid/nko') throw new Error('prefer nko');
  process.stdout.write('amplify self-test ok\n');
}

if (process.argv.includes('--self-test')) {
  selfTest();
} else {
  main().catch((err) => {
    console.error('\n🔴 エラー:', err.message);
    process.exit(1);
  });
}
