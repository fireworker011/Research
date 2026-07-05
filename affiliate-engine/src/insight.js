#!/usr/bin/env node
'use strict';

/**
 * Insight Engine（2〜3日サイクルの改善ループ）
 *
 * 1. 自アカウントの実測アナリティクス（top_posts / metrics_history）を集計
 * 2. Claude の Web 検索ツールで、稼働中ジャンルの「今バズっている投稿・トレンド」をリサーチ
 * 3. 実測と市場を突き合わせた改善レポート + 新テンプレ草案を生成
 *
 * 出力:
 * - output/insights/insight_YYYY-MM-DD.md   改善レポート（人間が読む）
 * - data/proposed_templates.json            新テンプレ草案（コンプライアンス通過分のみ）
 *
 * 草案の反映は人間のレビューを挟む設計:
 *   レポートを確認 → node src/apply-proposals.js で seed に統合＆スケジュール再生成
 *
 * 使用方法:
 *   ANTHROPIC_API_KEY=... node src/insight.js
 */

const fs = require('fs');
const path = require('path');
const { askClaude, extractJSON } = require('./claude-client');
const { checkContent } = require('./compliance');
const { ROOT, OUTPUT_DIR, readJSON, writeJSON, loadConfig, todayJST } = require('./util');

const SYSTEM_PROMPT = `あなたは日本のSNSアフィリエイト運用のグロースアナリストです。
遵守事項:
- テンプレ草案では誇大表現（絶対/必ず/100%/誰でも稼げる等）・効果効能の断定・性的訴求を書かない
- 体験談の捏造をしない（「私は3ヶ月で〜できた」等の具体的な偽の実体験は書かない。一般論・観察・提案の形にする）
- バズ投稿の「構造・切り口」を学ぶこと。文面のコピーや言い換えただけの模倣はしない
- リンクを含む草案は末尾に #PR を入れる
- 最終出力は指示された JSON のみ`;

/** 自アカウントの実測サマリを組み立てる */
function buildOwnAnalytics(activeGenres) {
  const topPosts = readJSON(path.join(OUTPUT_DIR, 'top_posts.json'), []);
  const historyPath = path.join(OUTPUT_DIR, 'metrics_history.jsonl');
  let history = [];
  if (fs.existsSync(historyPath)) {
    history = fs
      .readFileSync(historyPath, 'utf-8')
      .trim()
      .split('\n')
      .filter(Boolean)
      .map((line) => JSON.parse(line))
      .slice(-14);
  }

  const byGenre = {};
  for (const genre of activeGenres) {
    const posts = topPosts.filter((p) => p.genre === genre);
    const views = posts.map((p) => p.views || 0);
    byGenre[genre] = {
      sample_size: posts.length,
      avg_views: views.length ? Math.round(views.reduce((a, b) => a + b, 0) / views.length) : 0,
      top3: posts.slice(0, 3).map((p) => ({ views: p.views, likes: p.likes, text: (p.text || '').slice(0, 120) })),
      bottom3: posts.slice(-3).map((p) => ({ views: p.views, text: (p.text || '').slice(0, 120) }))
    };
  }
  return { byGenre, followers_history: history.map((h) => ({ date: h.date, followers: h.followers })) };
}

function buildPrompt(activeGenres, ownAnalytics, awarenessUntil) {
  const phaseNote =
    awarenessUntil && todayJST() < awarenessUntil
      ? `\n【現在のフェーズ】認知拡大フェーズ（〜${awarenessUntil}）。リンク誘導よりフォロワー獲得を最優先。
草案は「保存したくなる価値提供」「返信したくなる質問」「共感を呼ぶ観察」を中心にし、リンク入りは各ジャンル最大1本まで。\n`
      : '';
  return `Threads で運用中のアフィリエイトアカウント群の改善分析を行ってください。

【稼働中ジャンル】${activeGenres.join('、')}
${phaseNote}

【自アカウントの実測データ（直近）】
${JSON.stringify(ownAnalytics, null, 1)}

【タスク】
1. Web検索を使い、各ジャンルについて「直近2〜4週間で日本のThreads/SNSでバズっている投稿の傾向・切り口・話題」をリサーチする
   （検索例: 「Threads ${activeGenres[0]} バズ 投稿」「${activeGenres[0]} SNS 話題 今週」など。各ジャンル1〜2回検索）
2. 市場トレンドと自アカウントの実測（伸びた投稿/伸びなかった投稿）を突き合わせ、ジャンルごとに改善方針を出す
3. 各ジャンル2〜3本の新テンプレ草案を作る（学ぶのは構造・切り口のみ。文面の模倣は禁止。
   {{AFFILIATE_LINK}} + #PR 入りは各ジャンル最大1本、残りは価値提供。可能なら質問で締める）

【出力形式】以下の JSON のみ:
{
  "generated_for": "${todayJST()}",
  "genre_insights": [
    {
      "genre": "ジャンル名",
      "market_trends": ["市場で今バズっている切り口・話題を3〜5個、具体的に"],
      "own_performance_review": "実測データから読み取れること（1〜3文）",
      "actions": ["具体的な改善アクション2〜4個"],
      "new_templates": [
        { "id": "ジャンル英語名_${todayJST().replaceAll('-', '')}_連番", "genre": "ジャンル名", "content": "投稿本文", "emoji": "絵文字1〜3個", "engagement_prediction": "high/medium/low", "cta_type": "direct/implicit/none", "link_key": "リンク入りの場合のみ config/links.json のキー名" }
      ]
    }
  ],
  "overall_actions": ["アカウント横断の改善アクション"],
  "sources": ["参照したURL"]
}

利用可能な link_key: 婚活_相談所, 副業_ココナラ, 副業_A8, 副業_mixhost, 副業_FX, 美容_オルビスユー, 筋トレ_マッスルデリ, 筋トレ_HMB, 教育_ヒューマン`;
}

function renderMarkdown(data, complianceNotes) {
  const lines = [`# インサイトレポート ${data.generated_for || todayJST()}`, ''];
  for (const gi of data.genre_insights || []) {
    lines.push(`## ${gi.genre}`);
    lines.push('');
    lines.push('**市場トレンド（Web検索による）**');
    for (const t of gi.market_trends || []) lines.push(`- ${t}`);
    lines.push('');
    lines.push(`**自アカウント実測の所見**: ${gi.own_performance_review || '-'}`);
    lines.push('');
    lines.push('**改善アクション**');
    for (const a of gi.actions || []) lines.push(`- [ ] ${a}`);
    lines.push('');
    lines.push(`**新テンプレ草案**: ${ (gi.new_templates || []).length }本（data/proposed_templates.json に出力）`);
    lines.push('');
  }
  if ((data.overall_actions || []).length) {
    lines.push('## アカウント横断アクション');
    lines.push('');
    for (const a of data.overall_actions) lines.push(`- [ ] ${a}`);
    lines.push('');
  }
  if (complianceNotes.length) {
    lines.push('## コンプライアンスで破棄した草案');
    lines.push('');
    for (const n of complianceNotes) lines.push(`- ${n}`);
    lines.push('');
  }
  if ((data.sources || []).length) {
    lines.push('## 参照ソース');
    lines.push('');
    for (const s of data.sources) lines.push(`- ${s}`);
    lines.push('');
  }
  lines.push('---');
  lines.push('**反映方法**: 草案を確認 → `node src/apply-proposals.js` で seed_templates.json に統合しスケジュール再生成 → コミット');
  lines.push('');
  return lines.join('\n');
}

async function main() {
  console.log('🔎 Insight Engine 開始\n');

  const accountsConfig = loadConfig('accounts', { accounts: [] });
  const activeGenres = [
    ...new Set(accountsConfig.accounts.filter((a) => a.enabled !== false).map((a) => a.genre))
  ];
  if (activeGenres.length === 0) {
    console.error('❌ 有効なアカウントがありません');
    process.exit(1);
  }
  console.log(`  対象ジャンル: ${activeGenres.join(', ')}`);

  const ownAnalytics = buildOwnAnalytics(activeGenres);
  console.log('  実測データ読み込み完了。Claude（Web検索付き）で市場リサーチ中...\n');

  const response = await askClaude(buildPrompt(activeGenres, ownAnalytics, accountsConfig.awareness_until), {
    system: SYSTEM_PROMPT,
    maxTokens: 16000,
    tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: 8 }]
  });
  const data = extractJSON(response);

  // 草案のコンプライアンスフィルタ
  const complianceNotes = [];
  const proposals = [];
  for (const gi of data.genre_insights || []) {
    for (const t of gi.new_templates || []) {
      const result = checkContent(t.content || '');
      if (result.ok) {
        proposals.push({ ...t, content: result.text });
      } else {
        complianceNotes.push(`（${t.genre}）${result.reasons.join(', ')}: ${String(t.content).slice(0, 60)}...`);
      }
    }
  }

  const date = todayJST();
  const insightDir = path.join(OUTPUT_DIR, 'insights');
  fs.mkdirSync(insightDir, { recursive: true });
  const reportPath = path.join(insightDir, `insight_${date}.md`);
  fs.writeFileSync(reportPath, renderMarkdown(data, complianceNotes), 'utf-8');

  writeJSON(path.join(ROOT, 'data', 'proposed_templates.json'), {
    generated_at: new Date().toISOString(),
    note: 'insight.js による草案。レビュー後 node src/apply-proposals.js で反映',
    posting_templates: proposals
  });

  console.log(`✅ レポート: ${reportPath}`);
  console.log(`✅ テンプレ草案: ${proposals.length}本（破棄 ${complianceNotes.length}本） → data/proposed_templates.json`);
  console.log('\n次のステップ: レポート確認 → node src/apply-proposals.js で反映');
}

main().catch((err) => {
  console.error('\n🔴 エラー:', err.message);
  process.exit(1);
});
