#!/usr/bin/env node
'use strict';

/**
 * Threads アクセストークン 月次リフレッシュ（5アカウント対応）
 *
 * 長期トークン（60日）は自然には更新されないため、期限切れ前に
 * th_refresh_token でリフレッシュする。GitHub Actions の既定トークン
 * （GITHUB_TOKEN）には Secrets 書き換え権限がなく、これは GitHub の仕様上
 * 回避不可能なため、新トークンは Step Summary に出力 + Issue を1件作成し、
 * 人間が Secrets へ貼り直す運用にする（旧: konkatsu 単体版と同じ設計を5アカウントに拡張）。
 *
 * 使用方法:
 *   node src/refresh-tokens.js
 *
 * 環境変数: 各アカウントの THREADS_<KEY>_ACCESS_TOKEN、GITHUB_TOKEN、
 *          GITHUB_REPOSITORY、GITHUB_STEP_SUMMARY（Actions が自動設定）
 */

const fs = require('fs');
const { loadConfig } = require('./util');

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';
const GITHUB_REPOSITORY = process.env.GITHUB_REPOSITORY || '';
const GITHUB_SERVER_URL = process.env.GITHUB_SERVER_URL || 'https://github.com';
const GITHUB_RUN_ID = process.env.GITHUB_RUN_ID || '';
const STEP_SUMMARY = process.env.GITHUB_STEP_SUMMARY || '';

async function refreshToken(token) {
  const url = new URL('https://graph.threads.net/refresh_access_token');
  url.searchParams.set('grant_type', 'th_refresh_token');
  url.searchParams.set('access_token', token);
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`${res.status}: ${data.error?.message || JSON.stringify(data)}`);
  }
  const expiresIn = data.expires_in || 5184000; // 既定60日（秒）
  const expireDate = new Date(Date.now() + expiresIn * 1000).toISOString().split('T')[0];
  return { newToken: data.access_token, expireDate };
}

function writeSummary(results) {
  if (!STEP_SUMMARY) return;
  const lines = ['## Threads トークン リフレッシュ結果', ''];
  for (const r of results) {
    if (r.error) {
      lines.push(`### ❌ ${r.key}（${r.token_env}）`);
      lines.push(`失敗: ${r.error}`);
      lines.push('');
      continue;
    }
    lines.push(`### ✅ ${r.key}（${r.token_env}）`);
    lines.push(`次回期限: ${r.expireDate}`);
    lines.push('');
    lines.push('```');
    lines.push(r.newToken);
    lines.push('```');
    lines.push('');
  }
  fs.appendFileSync(STEP_SUMMARY, lines.join('\n') + '\n', 'utf-8');
}

async function createIssue(results) {
  if (!GITHUB_TOKEN || !GITHUB_REPOSITORY) return;
  const succeeded = results.filter((r) => !r.error);
  const failed = results.filter((r) => r.error);
  if (succeeded.length === 0 && failed.length === 0) return;

  const runUrl = `${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/actions/runs/${GITHUB_RUN_ID}`;
  const secretsUrl = `${GITHUB_SERVER_URL}/${GITHUB_REPOSITORY}/settings/secrets/actions`;

  const rows = succeeded.map((r) => `- \`${r.token_env}\` → 次回期限 ${r.expireDate}`).join('\n');
  const failRows = failed.map((r) => `- \`${r.token_env}\`: ${r.error}`).join('\n');

  const body = `## Threads アクセストークンの更新が必要です

トークンのリフレッシュが完了しました。新しいトークンは下記のワークフロー実行ログの **Summary** タブから確認できます。

### 手順
1. [ワークフロー実行ログ](${runUrl}) → Summary タブを開く
2. 対象アカウントの新しいトークンをコピー
3. [GitHub Secrets](${secretsUrl}) → 該当する \`THREADS_*_ACCESS_TOKEN\` を更新
4. このIssueをクローズ

### 更新対象
${rows || '（なし）'}
${failed.length ? `\n### ⚠️ 失敗（要確認・トークン失効の可能性）\n${failRows}\n` : ''}`;

  const res = await fetch(`https://api.github.com/repos/${GITHUB_REPOSITORY}/issues`, {
    method: 'POST',
    headers: {
      Authorization: `token ${GITHUB_TOKEN}`,
      Accept: 'application/vnd.github.v3+json',
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      title: `[要対応] Threads トークンを更新してください（${new Date().toISOString().slice(0, 7)}）`,
      body
    })
  });
  const data = await res.json().catch(() => ({}));
  if (res.ok) {
    console.log(`[Issue作成] ${data.html_url || ''}`);
  } else {
    console.warn(`[WARN] Issue作成失敗: ${res.status}`);
  }
}

async function main() {
  console.log('🔄 Threads トークン リフレッシュ開始\n');
  const accountsConfig = loadConfig('accounts', { accounts: [] });
  const results = [];

  for (const account of accountsConfig.accounts) {
    const token = process.env[account.token_env];
    if (!token) {
      console.log(`⏭  ${account.key}: ${account.token_env} が未設定のためスキップ`);
      continue;
    }
    try {
      const { newToken, expireDate } = await refreshToken(token);
      console.log(`✅ ${account.key}: リフレッシュ成功（次回期限 ${expireDate}）`);
      results.push({ key: account.key, token_env: account.token_env, newToken, expireDate });
    } catch (err) {
      console.log(`❌ ${account.key}: リフレッシュ失敗（${err.message}）`);
      results.push({ key: account.key, token_env: account.token_env, error: err.message });
    }
  }

  writeSummary(results);
  await createIssue(results);

  console.log(`\n完了: 成功 ${results.filter((r) => !r.error).length} / 失敗 ${results.filter((r) => r.error).length}`);
}

main().catch((err) => {
  console.error('\n🔴 エラー:', err.message);
  process.exit(1);
});
