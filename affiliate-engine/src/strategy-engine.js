#!/usr/bin/env node
'use strict';

/**
 * Strategy Engine
 * Claude で市場スコアリング + 投稿テンプレ生成 → 60日分の投稿スケジュール CSV を出力
 *
 * 元設計からの変更点:
 * - 「バズアカウントのリサーチ」は削除。API 経由の Claude はリアルタイムの
 *   SNS データを閲覧できず、架空のアカウント名・数値を生成してしまうため、
 *   捏造データで戦略判断するのは危険。代わりに実測メトリクス
 *   （output/top_posts.json、report.js が生成）を few-shot として使う改善ループを実装。
 * - 160本を1回の呼び出しで生成すると max_tokens で確実に切れるため、
 *   ジャンルごとに分割生成。
 * - 全テンプレは生成後にコンプライアンスチェックを通し、NG は破棄。
 *
 * 使用方法:
 *   ANTHROPIC_API_KEY=sk-ant-... node src/strategy-engine.js
 *
 *   API キーなしで手持ちのテンプレ JSON からスケジュールだけ組む場合:
 *   node src/strategy-engine.js --from-file data/seed_templates.json
 *   （フォーマット: { "market_analysis": [...], "posting_templates": [...] }）
 *
 * 環境変数:
 *   GENRES               対象ジャンル（デフォルト: 婚活,転職,美容,VOD,複合）
 *   TEMPLATES_PER_GENRE  ジャンルあたりのテンプレ数（デフォルト: 32）
 *   CAMPAIGN_DAYS        スケジュール日数（デフォルト: 60）
 *   POSTS_PER_DAY        1アカウントあたりの投稿数/日（デフォルト: 3）
 */

const fs = require('fs');
const path = require('path');
const { askClaude, extractJSON, sleep } = require('./claude-client');
const { checkContent } = require('./compliance');
const { OUTPUT_DIR, escapeCSV, readJSON, writeJSON, loadConfig, todayJST } = require('./util');

const GENRES = (process.env.GENRES || '婚活,副業,美容,筋トレ,教育,節約,転職,ペット,睡眠').split(',').map((g) => g.trim());
const TEMPLATES_PER_GENRE = parseInt(process.env.TEMPLATES_PER_GENRE || '32', 10);
const CAMPAIGN_DAYS = parseInt(process.env.CAMPAIGN_DAYS || '60', 10);
const POSTS_PER_DAY = parseInt(process.env.POSTS_PER_DAY || '3', 10);
const SCHEDULE_TIMES = ['07:00', '12:00', '19:00', '21:00'];

const SYSTEM_PROMPT = `あなたは日本のSNSアフィリエイトに精通したコンテンツストラテジストです。
遵守事項（違反した出力は破棄されます）:
- 誇大表現の禁止:「絶対」「必ず」「100%」「誰でも稼げる」等は使わない
- 薬機法: 美容系で効果効能を断定しない（「〜と感じた」「個人の感想」レベルに留める）
- アダルト・出会い系の性的訴求は書かない（Metaポリシー違反）
- 広告誘導を含む投稿には読者を騙す表現を使わない
- 出力は指示された JSON のみ。前置き・後置きテキストなし`;

/** ジャンル別の市場スコアリング（Claude の一般知識に基づく推定。実測ではない） */
async function analyzeMarket() {
  const prompt = `以下のアフィリエイトジャンルについて、日本市場での一般的な傾向を評価してください。
これはあなたの学習知識に基づく「推定」であり、実測データではないことを前提とします。

ジャンル: ${GENRES.join('、')}

各ジャンルについて JSON 配列で出力:
[
  {
    "genre": "ジャンル名",
    "demand_score": 1-10の整数,
    "typical_commission_jpy": 案件の典型的な単価（数値、円）,
    "typical_approval_rate": 典型的な承認率（数値、%）,
    "target_demographic": "主要ターゲット層",
    "content_angle": "Threadsで刺さりやすい切り口の説明",
    "caution": "このジャンルで注意すべき法規制・プラットフォーム規約"
  }
]`;
  const response = await askClaude(prompt, { system: SYSTEM_PROMPT, maxTokens: 4096 });
  return extractJSON(response);
}

/** 実測トップ投稿（report.js が出力）を few-shot 用に読み込む */
function loadTopPosts(genre) {
  const topPosts = readJSON(path.join(OUTPUT_DIR, 'top_posts.json'), []);
  return topPosts.filter((p) => p.genre === genre).slice(0, 3);
}

/** 1ジャンル分のテンプレ生成 */
async function generateTemplates(genre, marketInfo) {
  const topPosts = loadTopPosts(genre);
  const fewShot = topPosts.length
    ? `\n【実測で反応が良かった過去投稿（この型を参考に、コピーではなく新作を）】\n${topPosts
        .map((p) => `- (views: ${p.views}) ${p.text}`)
        .join('\n')}\n`
    : '';

  const prompt = `Threads 用の投稿テンプレを ${TEMPLATES_PER_GENRE} 本作成してください。

【ジャンル】${genre}
【市場情報】${JSON.stringify(marketInfo || {}, null, 0)}
${fewShot}
【投稿の要件】
- 250字以内。1行目で興味を掴む（質問・意外な事実・具体的な数字など）
- 体験談・気づき・具体的なノウハウ形式。宣伝臭を出さない
- 4本に1本程度のテンプレに {{AFFILIATE_LINK}} プレースホルダーを自然な文脈で含める
  （例:「詳しくはここにまとめた → {{AFFILIATE_LINK}}」）。残りは信頼構築用の価値提供
- 可能なら投稿の最後を「読者が答えたくなる質問」で締める（会話がアルゴリズム評価の中心）
- リンクを含むテンプレは末尾に「#PR」を必ず含める（景表法ステマ規制対応）
- リンクなしのテンプレは信頼構築用。CTAなしで価値提供に徹する
- 誇大表現・断定的な効果効能は禁止

JSON 配列のみで出力:
[
  {
    "id": "連番文字列",
    "genre": "${genre}",
    "content": "投稿本文（{{AFFILIATE_LINK}} と #PR を含む場合あり）",
    "emoji": "投稿末尾に添える絵文字1〜3個",
    "engagement_prediction": "high/medium/low",
    "cta_type": "direct/implicit/none"
  }
]`;

  const response = await askClaude(prompt, { system: SYSTEM_PROMPT, maxTokens: 16000 });
  const templates = extractJSON(response);

  // コンプライアンスフィルタ
  const passed = [];
  for (const t of templates) {
    const result = checkContent(t.content || '');
    if (result.ok) {
      passed.push({ ...t, content: result.text, genre });
    } else {
      console.warn(`  ⚠️ テンプレ破棄（${genre}）: ${result.reasons.join(', ')}`);
    }
  }
  return passed;
}

/** 開設日からの経過日数（created 未設定 = 十分に古い扱い） */
function accountAgeDays(created, date) {
  if (!created) return Infinity;
  return Math.floor((new Date(`${date}T00:00:00+09:00`) - new Date(`${created}T00:00:00+09:00`)) / 86400000);
}

/** 日付 → 通算日数（テンプレ選択を日付から決定論的に行うため） */
function epochDay(date) {
  return Math.floor(new Date(`${date}T00:00:00+09:00`).getTime() / 86400000);
}

/**
 * アカウント×日付×時刻でスケジュール CSV を組み立てる
 * - ランプアップ: 開設1週目は1本/日（19時）、2週目は2本/日（7時・19時）、以降フル
 *   （新規アカウントの急激な投稿開始はスパム判定・リーチ抑制の要因になるため）
 * - 認知フェーズ: awareness_until より前の日付にはリンク付きテンプレを割り当てない
 *   （最初の1ヶ月はフォロワー獲得・信頼構築に専念する運用方針）
 */
function buildScheduleCSV(templatesByGenre, accounts, { awarenessUntil = null } = {}) {
  const rows = [
    ['date', 'time', 'account', 'platform', 'genre', 'content', 'emoji', 'engagement_prediction', 'cta_type', 'link_key'].join(',')
  ];
  const times = SCHEDULE_TIMES.slice(0, POSTS_PER_DAY);

  for (let day = 0; day < CAMPAIGN_DAYS; day++) {
    const date = todayJST(day);
    const inAwareness = awarenessUntil && date < awarenessUntil;

    for (const account of accounts) {
      const age = accountAgeDays(account.created, date);
      const slotTimes =
        age < 7 ? times.slice(-1) : age < 14 ? [times[0], times[times.length - 1]] : times;

      // 「複合」アカウントは全ジャンルをローテーション
      const genrePool =
        account.genre === '複合' ? GENRES.filter((g) => g !== '複合') : [account.genre];

      for (let slot = 0; slot < slotTimes.length; slot++) {
        const genre = genrePool[(day + slot) % genrePool.length];
        let templates = templatesByGenre[genre] || templatesByGenre[account.genre] || [];
        if (inAwareness) {
          templates = templates.filter((t) => !String(t.content).includes('{{AFFILIATE_LINK}}'));
        }
        if (templates.length === 0) continue;

        // テンプレは「日付」から決定論的に選ぶ。
        // 以前は生成ごとに0リセットされるカーソル方式で、スケジュールを毎日
        // 再生成する運用に変えた際に毎日が「初日」となり、全アカウントが
        // 毎日同じテンプレを投稿する事故が起きた（2026-07-07〜09）。
        // 日付基準なら何度再生成しても同じ日には同じ選択になり、日ごとに進む。
        const idx = (epochDay(date) * slotTimes.length + slot) % templates.length;
        const t = templates[idx];

        rows.push(
          [
            date,
            slotTimes[slot],
            account.key,
            'threads',
            t.genre,
            escapeCSV(t.content),
            t.emoji || '',
            t.engagement_prediction || 'medium',
            t.cta_type || 'none',
            t.link_key || ''
          ].join(',')
        );
      }
    }
  }
  return rows.join('\n') + '\n';
}

async function main() {
  console.log('🚀 Strategy Engine 開始\n');
  console.log(`  ジャンル: ${GENRES.join(', ')}`);
  console.log(`  期間: ${CAMPAIGN_DAYS}日 × ${POSTS_PER_DAY}投稿/日/アカウント\n`);

  const accountsConfig = loadConfig('accounts', { accounts: [] });
  const accounts = accountsConfig.accounts.filter((a) => a.enabled !== false);
  if (accounts.length === 0) {
    console.error('❌ config/accounts.json に有効なアカウントがありません');
    process.exit(1);
  }

  const fromFileIdx = process.argv.indexOf('--from-file');
  const seedPath = fromFileIdx !== -1 ? path.resolve(process.argv[fromFileIdx + 1] || '') : null;

  let market = [];
  const templatesByGenre = {};

  if (seedPath) {
    console.log(`📂 テンプレをファイルから読み込み（API 呼び出しなし）: ${seedPath}\n`);
    const seed = readJSON(seedPath);
    if (!seed || !Array.isArray(seed.posting_templates)) {
      console.error('❌ シードファイルが読めないか posting_templates 配列がありません');
      process.exit(1);
    }
    market = seed.market_analysis || [];
    for (const t of seed.posting_templates) {
      const result = checkContent(t.content || '');
      if (!result.ok) {
        console.warn(`  ⚠️ テンプレ破棄（${t.genre}）: ${result.reasons.join(', ')}`);
        continue;
      }
      (templatesByGenre[t.genre] = templatesByGenre[t.genre] || []).push({
        ...t,
        content: result.text
      });
    }
    for (const [genre, list] of Object.entries(templatesByGenre)) {
      console.log(`  ${genre}: ${list.length}本`);
    }
  } else {
    console.log(`  テンプレ数: ${TEMPLATES_PER_GENRE}本/ジャンル × ${GENRES.length}ジャンル\n`);
    console.log('📊 ステップ1: 市場スコアリング（Claude 推定値）...');
    market = await analyzeMarket();
    for (const m of market) {
      console.log(`  ${m.genre}: 需要${m.demand_score}/10, 単価目安 ¥${m.typical_commission_jpy}`);
    }

    console.log('\n📝 ステップ2: テンプレ生成（ジャンル別）...');
    for (const genre of GENRES) {
      process.stdout.write(`  ${genre} ... `);
      const marketInfo = market.find((m) => m.genre === genre);
      templatesByGenre[genre] = await generateTemplates(genre, marketInfo);
      console.log(`${templatesByGenre[genre].length}本`);
      await sleep(1000);
    }
  }

  console.log('\n📋 ステップ3: スケジュール CSV 生成...');
  if (accountsConfig.awareness_until && todayJST() < accountsConfig.awareness_until) {
    console.log(`  🌱 認知フェーズ（〜${accountsConfig.awareness_until}）: リンク付き投稿は組み込みません`);
  }
  const csv = buildScheduleCSV(templatesByGenre, accounts, {
    awarenessUntil: accountsConfig.awareness_until || null
  });

  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
  const strategyPath = path.join(OUTPUT_DIR, 'strategy_data.json');
  const csvPath = path.join(OUTPUT_DIR, 'threads_posting_schedule.csv');

  writeJSON(strategyPath, {
    generated_at: new Date().toISOString(),
    note: 'market_analysis は Claude の一般知識による推定値。実測は report.js のメトリクスを正とする',
    genres: GENRES,
    market_analysis: market,
    posting_templates: Object.values(templatesByGenre).flat()
  });
  fs.writeFileSync(csvPath, csv, 'utf-8');

  console.log(`\n✅ 完了`);
  console.log(`  📊 ${strategyPath}`);
  console.log(`  📋 ${csvPath}`);
  console.log('\n次のステップ: node src/threads-poster.js --dry-run で投稿内容を確認');
}

main().catch((err) => {
  console.error('\n🔴 エラー:', err.message);
  process.exit(1);
});
