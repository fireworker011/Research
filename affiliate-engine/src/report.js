#!/usr/bin/env node
'use strict';

/**
 * KPI レポート
 *
 * 目標（月利30万円）に対する現在ペースを毎日可視化する。
 * ここが「現実的に達成する」ための心臓部:
 * 感覚ではなく実測ファネルでジャンル・投稿型の取捨選択を行う。
 *
 * 収集するもの:
 * - Threads Insights API: フォロワー数、投稿ごとの views/likes/replies/reposts
 * - data/conversions.csv: 確定円の正本（`approved_yen`）。カタログ・example の amount_jpy は円ではない。
 *
 * 出力:
 * - output/reports/report_YYYY-MM-DD.md   日次レポート
 * - output/top_posts.json                 高パフォーマンス投稿（strategy-engine の few-shot 用）
 * - output/metrics_history.jsonl          時系列メトリクス
 *
 * 使用方法:
 *   node src/report.js
 */

const fs = require('fs');
const path = require('path');
const { OUTPUT_DIR, parseCSV, readJSON, writeJSON, loadConfig, todayJST } = require('./util');

const THREADS_API = 'https://graph.threads.net/v1.0';
const TARGET_MONTHLY_JPY = parseInt(process.env.TARGET_MONTHLY_JPY || '300000', 10);

async function threadsGet(endpoint, params) {
  const url = new URL(`${THREADS_API}${endpoint}`);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`Threads API ${res.status}: ${data.error?.message || 'unknown'}`);
  }
  return data;
}

async function collectAccountMetrics(account) {
  const { userId, token } = account;
  const result = { key: account.key, genre: account.genre, followers: null, posts: [] };

  try {
    const insights = await threadsGet(`/${userId}/threads_insights`, {
      metric: 'followers_count',
      access_token: token
    });
    const followerMetric = (insights.data || []).find((m) => m.name === 'followers_count');
    result.followers = followerMetric?.total_value?.value ?? null;
  } catch (err) {
    console.warn(`  ⚠️ ${account.key}: フォロワー数取得失敗 (${err.message})`);
  }

  try {
    const media = await threadsGet(`/${userId}/threads`, {
      fields: 'id,text,timestamp,permalink',
      limit: '25',
      access_token: token
    });
    for (const post of media.data || []) {
      const metrics = { id: post.id, text: post.text, timestamp: post.timestamp, permalink: post.permalink };
      try {
        const ins = await threadsGet(`/${post.id}/insights`, {
          metric: 'views,likes,replies,reposts,quotes',
          access_token: token
        });
        for (const m of ins.data || []) {
          metrics[m.name] = m.values?.[0]?.value ?? m.total_value?.value ?? 0;
        }
      } catch (_) {
        // 直後の投稿は insights が無いことがある
      }
      result.posts.push(metrics);
    }
  } catch (err) {
    console.warn(`  ⚠️ ${account.key}: 投稿一覧取得失敗 (${err.message})`);
  }

  return result;
}

/** approved_yen だけを円にする。example の amount_jpy は足さない。 */
function approvedRows(rows) {
  const byGenre = {};
  let approvedTotal = 0;
  const pendingTotal = 0;
  let count = 0;
  for (const r of rows) {
    const d = String(r.date || '');
    if (d.startsWith('#')) continue;
    if (/カタログ/.test(String(r.note || '')) && parseInt(r.approved_yen || '0', 10) > 0) continue;
    if (r.approved_yen === undefined || r.approved_yen === '') continue;
    const amount = parseInt(r.approved_yen, 10);
    if (!Number.isFinite(amount)) continue;
    const key = r.program || r.genre || r.source || 'all';
    byGenre[key] = byGenre[key] || { approved: 0, pending: 0, count: 0 };
    byGenre[key].count++;
    byGenre[key].approved += amount;
    approvedTotal += amount;
    count++;
  }
  return { approvedTotal, pendingTotal, byGenre, count };
}

/** ASP 成果 CSV。正本は approved_yen。example の amount_jpy は円にしない。 */
function loadConversions() {
  const csvPath = path.join(OUTPUT_DIR, '..', 'data', 'conversions.csv');
  if (!fs.existsSync(csvPath)) return null;

  const rows = parseCSV(fs.readFileSync(csvPath, 'utf-8'));
  const thisMonth = todayJST().slice(0, 7); // YYYY-MM
  const monthly = rows.filter((r) => {
    const d = String(r.date || '');
    if (d.startsWith('#')) return false;
    return d.startsWith(thisMonth);
  });
  return approvedRows(monthly);
}

/** 目標との差分から必要アクションを逆算 */
function funnelGapAnalysis(conversions, totalViews) {
  const funnel = loadConfig('funnel', {
    avg_commission_jpy: 5000,
    approval_rate: 0.8,
    cvr_click_to_conversion: 0.015,
    ctr_view_to_click: 0.008
  });

  const requiredApproved = TARGET_MONTHLY_JPY;
  const requiredRaw = requiredApproved / funnel.approval_rate;
  const requiredConversions = Math.ceil(requiredRaw / funnel.avg_commission_jpy);
  const requiredClicks = Math.ceil(requiredConversions / funnel.cvr_click_to_conversion);
  const requiredViews = Math.ceil(requiredClicks / funnel.ctr_view_to_click);

  const dayOfMonth = parseInt(todayJST().split('-')[2], 10);
  const paceApproved = conversions ? Math.round((conversions.approvedTotal / dayOfMonth) * 30) : 0;

  return {
    funnel,
    requiredConversions,
    requiredClicks,
    requiredViews,
    requiredViewsPerDay: Math.ceil(requiredViews / 30),
    currentMonthApproved: conversions?.approvedTotal ?? 0,
    currentMonthPending: conversions?.pendingTotal ?? 0,
    projectedMonthly: paceApproved,
    gapJpy: TARGET_MONTHLY_JPY - paceApproved,
    totalViewsRecent: totalViews
  };
}

function renderReport(date, accountMetrics, conversions, gap) {
  const lines = [];
  lines.push(`# 日次レポート ${date}`);
  lines.push('');
  lines.push(`## 収益（目標: ¥${TARGET_MONTHLY_JPY.toLocaleString()}/月）`);
  lines.push('');
  if (conversions) {
    lines.push(`- 今月の確定報酬: **¥${conversions.approvedTotal.toLocaleString()}**`);
    lines.push(`- 今月の未確定報酬: ¥${conversions.pendingTotal.toLocaleString()}`);
    lines.push(`- 月末着地予測（現在ペース）: **¥${gap.projectedMonthly.toLocaleString()}**`);
    lines.push(`- 目標との差: ¥${gap.gapJpy.toLocaleString()}`);
    lines.push('');
    lines.push('### ジャンル別');
    lines.push('');
    lines.push('| ジャンル | 件数 | 確定 | 未確定 |');
    lines.push('|---|---|---|---|');
    for (const [genre, v] of Object.entries(conversions.byGenre)) {
      lines.push(`| ${genre} | ${v.count} | ¥${v.approved.toLocaleString()} | ¥${v.pending.toLocaleString()} |`);
    }
  } else {
    lines.push('- ⚠️ `data/conversions.csv` がありません。Issue `Affiliate — 確定円` に `A8_YEN:` を書くか、画面を見た行だけ置く。');
    lines.push('  （正本: `date,source,program,clicks,cv,approved_yen,note`。カタログ円は足すな）');
  }
  lines.push('');
  lines.push('## 必要ファネル（目標達成に必要な月間数値）');
  lines.push('');
  lines.push(`- 成約: ${gap.requiredConversions} 件/月（単価 ¥${gap.funnel.avg_commission_jpy.toLocaleString()}・承認率 ${gap.funnel.approval_rate * 100}% 想定）`);
  lines.push(`- クリック: ${gap.requiredClicks.toLocaleString()} 回/月（CVR ${gap.funnel.cvr_click_to_conversion * 100}% 想定）`);
  lines.push(`- ビュー: ${gap.requiredViews.toLocaleString()} 回/月 = **${gap.requiredViewsPerDay.toLocaleString()} 回/日**（CTR ${gap.funnel.ctr_view_to_click * 100}% 想定）`);
  lines.push('');
  lines.push('※ CTR/CVR は config/funnel.json の想定値。短縮URL の実測クリック数が取れたら更新すること');
  lines.push('');
  lines.push('## アカウント別メトリクス');
  lines.push('');
  lines.push('| アカウント | ジャンル | フォロワー | 直近25投稿の合計views | 平均views/投稿 |');
  lines.push('|---|---|---|---|---|');
  for (const acc of accountMetrics) {
    const views = acc.posts.reduce((sum, p) => sum + (p.views || 0), 0);
    const avg = acc.posts.length ? Math.round(views / acc.posts.length) : 0;
    lines.push(`| ${acc.key} | ${acc.genre} | ${acc.followers ?? '-'} | ${views.toLocaleString()} | ${avg.toLocaleString()} |`);
  }
  lines.push('');
  lines.push('## 判断ルール（週次で確認）');
  lines.push('');
  lines.push('- 平均views/投稿 が全体平均の半分未満のジャンル → テンプレ再生成 or 停止して他ジャンルに再配分');
  lines.push('- 上位投稿の型は `output/top_posts.json` 経由で次回テンプレ生成の few-shot に自動反映される');
  lines.push('- Day30 時点で確定報酬 ¥30,000 未満 → 案件（ASP オファー）自体を入れ替える');
  lines.push('');
  return lines.join('\n');
}

async function main() {
  console.log('📊 KPI レポート生成\n');

  const accountsConfig = loadConfig('accounts', { accounts: [] });
  const accounts = accountsConfig.accounts
    .filter((a) => a.enabled !== false)
    .map((a) => ({
      ...a,
      userId: process.env[a.user_id_env],
      token: process.env[a.token_env]
    }))
    .filter((a) => a.userId && a.token);

  if (accounts.length === 0) {
    console.warn('⚠️ トークン設定済みのアカウントがありません。収益集計のみ実行します');
  }

  const accountMetrics = [];
  for (const account of accounts) {
    console.log(`  収集中: ${account.key}`);
    accountMetrics.push(await collectAccountMetrics(account));
  }

  const conversions = loadConversions();
  const totalViews = accountMetrics.reduce(
    (sum, a) => sum + a.posts.reduce((s, p) => s + (p.views || 0), 0),
    0
  );
  const gap = funnelGapAnalysis(conversions, totalViews);

  // トップ投稿を few-shot 用に保存（views 上位、ジャンル情報付き）
  const allPosts = accountMetrics.flatMap((a) =>
    a.posts.filter((p) => p.views).map((p) => ({ genre: a.genre, views: p.views, likes: p.likes || 0, text: p.text }))
  );
  allPosts.sort((a, b) => b.views - a.views);
  writeJSON(path.join(OUTPUT_DIR, 'top_posts.json'), allPosts.slice(0, 15));

  // 時系列に追記（1日1エントリ。同日再実行時は上書きし、重複行を作らない）
  const historyPath = path.join(OUTPUT_DIR, 'metrics_history.jsonl');
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const todayEntry = JSON.stringify({
    date: todayJST(),
    followers: Object.fromEntries(accountMetrics.map((a) => [a.key, a.followers])),
    total_views_recent: totalViews,
    approved_jpy: conversions?.approvedTotal ?? null,
    pending_jpy: conversions?.pendingTotal ?? null
  });
  const historyLines = fs.existsSync(historyPath)
    ? fs.readFileSync(historyPath, 'utf-8').split('\n').filter(Boolean)
    : [];
  const kept = historyLines.filter((line) => {
    try {
      return JSON.parse(line).date !== todayJST();
    } catch (_) {
      return true;
    }
  });
  kept.push(todayEntry);
  fs.writeFileSync(historyPath, kept.join('\n') + '\n', 'utf-8');

  // レポート出力
  const date = todayJST();
  const reportDir = path.join(OUTPUT_DIR, 'reports');
  fs.mkdirSync(reportDir, { recursive: true });
  const reportPath = path.join(reportDir, `report_${date}.md`);
  fs.writeFileSync(reportPath, renderReport(date, accountMetrics, conversions, gap), 'utf-8');

  console.log(`\n✅ レポート出力: ${reportPath}`);
  console.log(`   月末着地予測: ¥${gap.projectedMonthly.toLocaleString()} / 目標 ¥${TARGET_MONTHLY_JPY.toLocaleString()}`);
}

function selfTest() {
  const example = parseCSV('date,genre,amount_jpy,status\n2026-07-01,転職,12000,approved\n');
  if (approvedRows(example).approvedTotal !== 0) throw new Error('example yen');
  const live = parseCSV('date,source,program,clicks,cv,approved_yen,note\n2026-08-27,A8,all,33,0,0,x\n');
  if (approvedRows(live).approvedTotal !== 0) throw new Error('zero row');
  const cat = parseCSV('date,source,program,clicks,cv,approved_yen,note\n2026-09-09,A8,all,1,0,15000,カタログ\n');
  if (approvedRows(cat).approvedTotal !== 0) throw new Error('catalog');
  const ok = parseCSV('date,source,program,clicks,cv,approved_yen,note\n2026-09-09,A8,all,1,1,5000,screen\n');
  if (approvedRows(ok).approvedTotal !== 5000) throw new Error('real yen');
  process.stdout.write('report self-test ok\n');
}

if (process.argv.includes('--self-test')) {
  selfTest();
} else {
  main().catch((err) => {
    console.error('\n🔴 エラー:', err.message);
    process.exit(1);
  });
}
