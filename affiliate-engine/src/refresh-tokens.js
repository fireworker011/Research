#!/usr/bin/env node
'use strict';

/**
 * Threads アクセストークン 月次リフレッシュ（5アカウント対応）
 *
 * 長期トークン（60日）は自然には更新されないため、期限切れ前に
 * th_refresh_token でリフレッシュする。
 *
 * Secrets への書き戻し:
 * - GH_SECRETS_PAT（Secrets 書き換え権限を持つ Fine-grained PAT）が設定されて
 *   いれば、gh CLI 経由で THREADS_*_ACCESS_TOKEN を自動更新する（完全自動）。
 * - 未設定または書き戻し失敗時は、従来どおり Step Summary に新トークンを出力し
 *   Issue を作成して人間に手動更新を依頼する（フォールバック）。
 *   （GitHub Actions の既定トークンには Secrets 書き換え権限がなく、これは
 *     GitHub の仕様上 PAT なしでは回避不可能）
 *
 * 使用方法:
 *   node src/refresh-tokens.js
 *
 * 環境変数: 各アカウントの THREADS_<KEY>_ACCESS_TOKEN、GITHUB_TOKEN、
 *          GITHUB_REPOSITORY、GITHUB_STEP_SUMMARY（Actions が自動設定）、
 *          GH_SECRETS_PAT（任意・自動書き戻し用）
 */

const fs = require('fs');
const { spawnSync } = require('child_process');
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

/** gh CLI で Secrets を書き戻す（トークンは stdin 経由で渡し、引数に露出させない） */
function updateSecret(name, value) {
  const pat = process.env.GH_SECRETS_PAT;
  if (!pat) return { ok: false, reason: 'GH_SECRETS_PAT 未設定' };
  const res = spawnSync('gh', ['secret', 'set', name, '--repo', GITHUB_REPOSITORY], {
    input: value,
    env: { ...process.env, GH_TOKEN: pat },
    encoding: 'utf-8',
    timeout: 30000
  });
  if (res.status === 0) return { ok: true };
  return { ok: false, reason: (res.stderr || res.error?.message || `exit ${res.status}`).trim() };
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
    if (r.secretUpdated) {
      // 自動書き戻し成功時はトークンをログに出さない
      lines.push(`### ✅ ${r.key}（${r.token_env}）: Secrets 自動更新済み・次回期限 ${r.expireDate}`);
      lines.push('');
      continue;
    }
    lines.push(`### ⚠️ ${r.key}（${r.token_env}）: 手動更新が必要（自動書き戻し不可: ${r.secretUpdateError || '-'}）`);
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
  // 自動書き戻しが全件成功していれば人間の作業はゼロ → Issue は立てない
  const succeeded = results.filter((r) => !r.error && !r.secretUpdated);
  const failed = results.filter((r) => r.error);
  if (succeeded.length === 0 && failed.length === 0) {
    console.log('（全件自動更新済みのため Issue は作成しません）');
    return;
  }

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
      const result = { key: account.key, token_env: account.token_env, newToken, expireDate };
      const update = updateSecret(account.token_env, newToken);
      if (update.ok) {
        result.secretUpdated = true;
        console.log(`✅ ${account.key}: リフレッシュ + Secrets 自動更新 完了（次回期限 ${expireDate}）`);
      } else {
        result.secretUpdateError = update.reason;
        console.log(`⚠️ ${account.key}: リフレッシュ成功・Secrets 自動更新は不可（${update.reason}）→ Issue で手動更新を依頼`);
      }
      results.push(result);
    } catch (err) {
      console.log(`❌ ${account.key}: リフレッシュ失敗（${err.message}）`);
      results.push({ key: account.key, token_env: account.token_env, error: err.message });
    }
  }

  writeSummary(results);
  await createIssue(results);

  const auto = results.filter((r) => r.secretUpdated).length;
  console.log(`\n完了: リフレッシュ成功 ${results.filter((r) => !r.error).length}（うち自動書き戻し ${auto}）/ 失敗 ${results.filter((r) => r.error).length}`);
}

main().catch((err) => {
  console.error('\n🔴 エラー:', err.message);
  process.exit(1);
});
