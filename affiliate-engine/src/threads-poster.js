#!/usr/bin/env node
'use strict';

/**
 * Threads Poster（ステートレス版）
 *
 * 元設計（node-schedule 常駐）からの変更点:
 * - 常駐プロセスは PC 再起動・スリープで全停止するため、
 *   「実行時に期日が来ている未投稿分だけ投稿して終了する」方式に変更。
 *   GitHub Actions の cron から1日数回起動するだけで運用できる。
 * - 元コードはアクセストークンを一切送信しておらず全投稿が失敗する状態
 *   だった。Threads API の正規フロー（①コンテナ作成 → ②公開）を実装。
 * - 投稿前に compliance.js を通し、#PR 表記の自動付与と NG 表現ブロックを行う。
 *
 * 使用方法:
 *   node src/threads-poster.js [--dry-run]
 *
 * 環境変数:
 *   各アカウントの user_id / access_token（config/accounts.json の env 名で指定）
 *   CATCHUP_HOURS   何時間前までの未投稿分を拾うか（デフォルト: 6）
 *   DAILY_CAP       1アカウントの1日最大投稿数（デフォルト: 10、API上限は250）
 */

const fs = require('fs');
const path = require('path');
const { checkContent } = require('./compliance');
const {
  OUTPUT_DIR,
  parseCSV,
  readJSON,
  writeJSON,
  loadConfig,
  todayJST,
  scheduleEpoch
} = require('./util');
const { sleep } = require('./claude-client');

const THREADS_API = 'https://graph.threads.net/v1.0';
const CATCHUP_HOURS = parseFloat(process.env.CATCHUP_HOURS || '6');
const DAILY_CAP = parseInt(process.env.DAILY_CAP || '10', 10);
const STATE_PATH = path.join(OUTPUT_DIR, 'state', 'posted.json');
const CSV_PATH = process.env.SCHEDULE_CSV || path.join(OUTPUT_DIR, 'threads_posting_schedule.csv');

const isDryRun = process.argv.includes('--dry-run');

/** Threads API 呼び出し（トークンはクエリパラメータで送信する仕様） */
async function threadsPost(endpoint, params) {
  const url = new URL(`${THREADS_API}${endpoint}`);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }
  const res = await fetch(url, { method: 'POST' });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`Threads API ${res.status}: ${data.error?.message || JSON.stringify(data)}`);
  }
  return data;
}

/** 正規の2ステップ投稿: コンテナ作成 → 公開 */
async function publishToThreads(userId, accessToken, text) {
  const container = await threadsPost(`/${userId}/threads`, {
    media_type: 'TEXT',
    text,
    access_token: accessToken
  });
  // Meta 推奨: コンテナ処理待ち
  await sleep(2000);
  const published = await threadsPost(`/${userId}/threads_publish`, {
    creation_id: container.id,
    access_token: accessToken
  });
  return published.id;
}

function rowKey(row) {
  return `${row.date}_${row.time}_${row.account}`;
}

/** 投稿本文を組み立てる。リンク必須なのに未設定なら null（=スキップ） */
function buildPostText(row, links) {
  let text = row.content || '';
  // 案件別キー（link_key）優先、なければジャンル共通リンク
  const link = links[row.link_key] || links[row.genre];

  if (text.includes('{{AFFILIATE_LINK}}')) {
    if (!link) {
      // 文脈ごと壊れるためリンク未設定のテンプレは投稿しない
      return null;
    }
    text = text.replaceAll('{{AFFILIATE_LINK}}', link);
  }
  if (row.emoji && !text.endsWith(row.emoji)) {
    text = `${text}\n${row.emoji}`;
  }
  return text.trim();
}

function logPosting(entry) {
  const logDir = path.join(OUTPUT_DIR, 'posting_logs');
  fs.mkdirSync(logDir, { recursive: true });
  const logPath = path.join(logDir, `posting_${todayJST()}.jsonl`);
  fs.appendFileSync(logPath, JSON.stringify(entry) + '\n', 'utf-8');
}

async function main() {
  console.log(`🚀 Threads Poster ${isDryRun ? '（ドライラン）' : ''}\n`);

  if (!fs.existsSync(CSV_PATH)) {
    console.error(`❌ スケジュール CSV がありません: ${CSV_PATH}`);
    console.error('   先に node src/strategy-engine.js を実行してください');
    process.exit(1);
  }

  const accountsConfig = loadConfig('accounts', { accounts: [] });
  const accounts = Object.fromEntries(
    accountsConfig.accounts
      .filter((a) => a.enabled !== false)
      .map((a) => [
        a.key,
        {
          ...a,
          userId: process.env[a.user_id_env],
          token: process.env[a.token_env]
        }
      ])
  );
  const links = loadConfig('links', {});

  const schedule = parseCSV(fs.readFileSync(CSV_PATH, 'utf-8'));
  const state = readJSON(STATE_PATH, { posted: {} });

  const now = Date.now();
  const windowStart = now - CATCHUP_HOURS * 3600 * 1000;

  // 今日すでに投稿した数（デイリーキャップ用）
  const today = todayJST();
  const postedToday = {};
  for (const [key, entry] of Object.entries(state.posted)) {
    if (entry.status === 'success' && key.startsWith(today)) {
      const account = key.split('_').slice(2).join('_');
      postedToday[account] = (postedToday[account] || 0) + 1;
    }
  }

  const due = schedule.filter((row) => {
    const t = scheduleEpoch(row.date, row.time);
    return t <= now && t >= windowStart && !state.posted[rowKey(row)];
  });

  console.log(`📋 スケジュール ${schedule.length} 件中、投稿対象 ${due.length} 件\n`);

  let success = 0;
  let failed = 0;
  let skipped = 0;

  for (const row of due) {
    const key = rowKey(row);
    const account = accounts[row.account];
    const label = `${row.date} ${row.time} @${row.account} (${row.genre})`;

    if (!account) {
      console.log(`⏭  ${label}: アカウント未定義のためスキップ`);
      skipped++;
      continue;
    }
    if ((postedToday[row.account] || 0) >= DAILY_CAP) {
      console.log(`⏭  ${label}: デイリー上限 ${DAILY_CAP} 件に到達`);
      skipped++;
      continue;
    }

    let text = buildPostText(row, links);
    if (text === null) {
      console.log(`⏭  ${label}: config/links.json に「${row.genre}」のリンク未設定のためスキップ`);
      if (!isDryRun) {
        state.posted[key] = { status: 'skipped_no_link', at: new Date().toISOString() };
      }
      skipped++;
      continue;
    }

    const compliance = checkContent(text);
    if (!compliance.ok) {
      console.log(`🚫 ${label}: コンプライアンスブロック（${compliance.reasons.join(', ')}）`);
      if (!isDryRun) {
        state.posted[key] = { status: 'blocked', reasons: compliance.reasons, at: new Date().toISOString() };
        logPosting({ key, status: 'blocked', reasons: compliance.reasons, text });
      }
      skipped++;
      continue;
    }
    text = compliance.text;

    if (isDryRun) {
      console.log(`📝 ${label}`);
      console.log(text.split('\n').map((l) => `   │ ${l}`).join('\n'));
      console.log('');
      continue;
    }

    if (!account.userId || !account.token) {
      console.log(`⏭  ${label}: ${account.user_id_env} / ${account.token_env} が未設定`);
      skipped++;
      continue;
    }

    try {
      const postId = await publishToThreads(account.userId, account.token, text);
      console.log(`✅ ${label}: 投稿成功 (${postId})`);
      state.posted[key] = { status: 'success', post_id: postId, at: new Date().toISOString() };
      logPosting({ key, status: 'success', post_id: postId, genre: row.genre, account: row.account });
      postedToday[row.account] = (postedToday[row.account] || 0) + 1;
      success++;
      await sleep(3000); // レート制限マージン
    } catch (err) {
      console.log(`❌ ${label}: ${err.message}`);
      state.posted[key] = { status: 'failed', error: err.message, at: new Date().toISOString() };
      logPosting({ key, status: 'failed', error: err.message, account: row.account });
      failed++;
    }
  }

  if (!isDryRun) {
    writeJSON(STATE_PATH, state);
    console.log(`\n📊 結果: 成功 ${success} / 失敗 ${failed} / スキップ ${skipped}`);
    console.log(`   状態ファイル: ${STATE_PATH}`);
  } else {
    console.log(`（ドライラン: ${due.length} 件が投稿対象でした。実投稿は行っていません）`);
  }

  // 失敗があっても他アカウントの投稿は完了しているため正常終了とし、
  // ログとレポートで検知する
}

main().catch((err) => {
  console.error('\n🔴 致命的エラー:', err.message);
  process.exit(1);
});
