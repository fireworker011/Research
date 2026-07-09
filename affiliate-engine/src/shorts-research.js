#!/usr/bin/env node
'use strict';

/**
 * YouTube Shorts リサーチ&ネタ出しエンジン（半自動）
 *
 * Threads 向けの insight.js と同じ「実測 × Web検索リサーチ」の構えを
 * YouTube Shorts 用に持ち込む。自動化するのはリサーチとネタ出しまでで、
 * 動画化・アップロードの判断は人間が行う（＝半自動）。
 *
 * 1. config/youtube.json のチャンネル別に、Claude の Web 検索で
 *    「直近の日本の Shorts で伸びている傾向・フック・フォーマット」をリサーチ
 * 2. 同ジャンルの Threads 実測データ（top_posts.json）を補助シグナルとして注入
 * 3. 台本レベルのネタ（タイトル / 冒頭2秒のフック / 30〜45秒ナレーション /
 *    ハッシュタグ / CTA / アフィリエイトリンク）を生成し、コンプライアンス検査
 * 4. 過去に出したネタ（data/shorts_ideas_history.jsonl）をプロンプトに渡して重複を回避
 *
 * 出力:
 * - output/shorts/ideas_YYYY-MM-DD.md   ネタ出しキット（人間が読む・Issue にも配信）
 * - data/shorts_proposed_ideas.json     採用待ちネタ（video-semi-auto.js --ideas が読む）
 * - data/shorts_ideas_history.jsonl     重複回避用の履歴
 *
 * 使用方法:
 *   ANTHROPIC_API_KEY=... node src/shorts-research.js                 # ネタ出し
 *   ANTHROPIC_API_KEY=... node src/shorts-research.js --select-genre  # 第三弾ジャンル選定リサーチ
 */

const fs = require('fs');
const path = require('path');
const { askClaude, extractJSON } = require('./claude-client');
const { checkContent } = require('./compliance');
const { ROOT, OUTPUT_DIR, readJSON, writeJSON, loadConfig, todayJST } = require('./util');

const SHORTS_DIR = path.join(OUTPUT_DIR, 'shorts');
const PROPOSED_PATH = path.join(ROOT, 'data', 'shorts_proposed_ideas.json');
const HISTORY_PATH = path.join(ROOT, 'data', 'shorts_ideas_history.jsonl');

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';
const GITHUB_REPOSITORY = process.env.GITHUB_REPOSITORY || '';
const TRACKING_ISSUE_TITLE = '🎬 YouTube Shorts ネタ出しキット';

const SYSTEM_PROMPT = `あなたは日本の YouTube Shorts 運用のグロースアナリスト兼放送作家です。
遵守事項:
- 誇大表現（絶対/必ず/100%/誰でも稼げる等）・効果効能の断定・性的訴求を書かない
- 体験談の捏造をしない（具体的な偽の実体験は書かない。一般論・観察・提案の形にする）
- 伸びている動画から学ぶのは「構造・フック・切り口」のみ。文面のコピーや言い換えただけの模倣はしない
- 台本は顔出しなし（テキスト+ナレーション+素材映像）で撮影できる構成にする
- アフィリエイト誘導を含む場合、概要欄に #PR を入れる前提で CTA を書く
- 最終出力は指示された JSON のみ`;

/** 同ジャンルの Threads 実測データを補助シグナルとして組み立てる */
function buildThreadsSignal(threadsGenre) {
  if (!threadsGenre) return null;
  const topPosts = readJSON(path.join(OUTPUT_DIR, 'top_posts.json'), []);
  const posts = topPosts.filter((p) => p.genre === threadsGenre);
  if (posts.length === 0) return null;
  const views = posts.map((p) => p.views || 0);
  return {
    note: `同ジャンルで運用中の Threads アカウントの実測（Shorts ではないが、刺さる切り口の参考シグナル）`,
    sample_size: posts.length,
    avg_views: Math.round(views.reduce((a, b) => a + b, 0) / views.length),
    top3: posts.slice(0, 3).map((p) => ({ views: p.views, likes: p.likes, text: (p.text || '').slice(0, 120) })),
    bottom3: posts.slice(-3).map((p) => ({ views: p.views, text: (p.text || '').slice(0, 120) }))
  };
}

/** 重複回避用に、そのチャンネルで過去に出したネタのタイトルを返す */
function loadRecentTitles(channelKey, limit = 40) {
  if (!fs.existsSync(HISTORY_PATH)) return [];
  return fs
    .readFileSync(HISTORY_PATH, 'utf-8')
    .trim()
    .split('\n')
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch (_) {
        return null;
      }
    })
    .filter((e) => e && e.channel === channelKey)
    .slice(-limit)
    .map((e) => e.title);
}

/** links.json に定義済みのキー一覧（ネタのリンク誘導先として提示する） */
function availableLinkKeys() {
  const links = loadConfig('links', {});
  return Object.keys(links).filter((k) => !k.startsWith('_'));
}

/**
 * 1チャンネル分のネタ出しプロンプト。
 * insight.js と同じ理由（Web検索の引用込みで max_tokens 超過 → JSON 破損）で
 * チャンネル別に分割して呼び出す。
 */
function buildChannelPrompt(channel, ideasPerChannel, threadsSignal, recentTitles) {
  const date = todayJST();
  const candidateNote =
    channel.status === 'candidate'
      ? '\n【注意】このチャンネルは開設検討中。ネタは「初投稿〜最初の2週間」を想定し、チャンネルの世界観が立ち上がる自己完結型を優先する。\n'
      : '';
  return `YouTube Shorts で運用する「${channel.genre}」ジャンルのチャンネル向けに、市場リサーチと投稿ネタ出しを行ってください。
${candidateNote}
【同ジャンルの Threads 実測データ（補助シグナル）】
${JSON.stringify(threadsSignal || '（データなし）', null, 1)}

【過去に出したネタのタイトル（重複・類似回避）】
${JSON.stringify(recentTitles, null, 1)}

【タスク】
1. Web検索（1〜2回）で「直近2〜4週間で日本の YouTube Shorts の${channel.genre}ジャンルで伸びている動画の傾向・フック・フォーマット・話題」をリサーチする
2. 市場トレンドと補助シグナルを突き合わせ、伸びている「構成の型」を特定する
3. 顔出しなしで制作できる Shorts のネタを${ideasPerChannel}本作る。各ネタは:
   - 冒頭2秒で離脱させないフック（画面テキスト or ナレーション第一声）
   - 30〜45秒のナレーション台本（そのまま読み上げられる完成文）
   - アフィリエイト誘導するネタは最大2本まで。残りは登録・保存を狙う価値提供型
   - 誘導する場合は下記の link_key から選ぶ（概要欄リンク前提の自然な CTA にする）

【利用可能な link_key】${availableLinkKeys().join(', ')}

【出力形式】以下の JSON のみ（前置き・後置きテキストなし）:
{
  "channel": "${channel.key}",
  "genre": "${channel.genre}",
  "market_trends": ["市場で今伸びている切り口・話題を3〜5個、具体的に"],
  "winning_formats": ["伸びている構成の型を2〜4個（例: 冒頭で結論→理由3つ→意外な落ち）"],
  "ideas": [
    {
      "id": "shorts_${channel.key}_${date.replaceAll('-', '')}_連番",
      "title": "YouTubeタイトル（検索とフィードの両方を意識、32字以内）",
      "hook": "冒頭2秒のフック（画面テキスト/第一声）",
      "script": "30〜45秒のナレーション全文",
      "scenes": ["映像の指定を時系列で3〜6個（顔出しなしで撮れる/素材で賄える指定）"],
      "hashtags": ["#ハッシュタグ3〜5個"],
      "cta": "締めの一言（誘導ネタなら概要欄リンクへ、価値提供ネタなら登録・保存へ）",
      "link_key": "リンク誘導する場合のみ上記キーから。しない場合は null",
      "engagement_prediction": "high/medium/low"
    }
  ],
  "sources": ["参照したURL"]
}`;
}

/** 第三弾（新チャンネル）のジャンル選定リサーチ用プロンプト */
function buildGenreSelectionPrompt(channels) {
  const active = channels.filter((c) => c.status === 'active').map((c) => c.genre);
  const topPosts = readJSON(path.join(OUTPUT_DIR, 'top_posts.json'), []);
  const byGenre = {};
  for (const p of topPosts) {
    if (!byGenre[p.genre]) byGenre[p.genre] = { posts: 0, total_views: 0 };
    byGenre[p.genre].posts++;
    byGenre[p.genre].total_views += p.views || 0;
  }
  return `YouTube Shorts のアフィリエイトチャンネル第三弾のジャンルを選定するためのリサーチを行ってください。

【前提】
- 既存チャンネル: ${active.join(' / ')}（既存と競合しないこと）
- 顔出しなし・テキスト+ナレーション+素材映像で制作する
- 収益はアフィリエイト（概要欄リンク）が主。提携可能な案件があるジャンルに限る
- 利用可能なアフィリエイトリンクのキー: ${availableLinkKeys().join(', ')}

【参考: 同オーナーの Threads 運用のジャンル別実測】
${JSON.stringify(byGenre, null, 1)}

【タスク】
1. Web検索（2〜3回）で、2026年時点の日本の YouTube Shorts で「顔出しなしで伸びやすく、アフィリエイト転換しやすい」ジャンルをリサーチする
2. 上記リンクキーに対応するジャンルから候補を3〜4個挙げ、市場規模・競合飽和度・案件単価・制作難易度で比較する
3. 最も推薦できるジャンルを1つ決め、チャンネル名案とコンセプトまで提案する

【出力形式】以下の JSON のみ:
{
  "candidates": [
    { "genre": "ジャンル名", "market": "市場・伸びやすさの所見", "competition": "競合飽和度", "affiliate_fit": "使える案件と単価感", "production": "制作難易度", "verdict": "推薦度 A/B/C と一言" }
  ],
  "recommendation": {
    "genre": "推薦ジャンル",
    "threads_genre": "対応する Threads ジャンル名（実測参照用）",
    "concept": "チャンネルコンセプト（2〜3文）",
    "channel_name_ideas": ["名前案を3個"],
    "first_week_direction": "最初の1週間の投稿方針（2〜3文）"
  },
  "sources": ["参照したURL"]
}`;
}

/** ネタ出しキットの Markdown を組み立てる */
function renderIdeasMarkdown(date, results, complianceNotes) {
  const lines = [`# 🎬 Shorts ネタ出しキット ${date}`, ''];
  lines.push('採用するネタを選んで `node src/video-semi-auto.js --ideas` で動画化 → YouTube Studio で予約投稿。');
  lines.push('');
  for (const r of results) {
    const statusMark = r.status === 'candidate' ? '（開設検討中）' : '';
    lines.push(`## ${r.genre}${statusMark} — @${r.handle || r.channel}`);
    lines.push('');
    lines.push('**市場トレンド（Web検索による）**');
    for (const t of r.market_trends || []) lines.push(`- ${t}`);
    lines.push('');
    lines.push('**伸びている構成の型**');
    for (const f of r.winning_formats || []) lines.push(`- ${f}`);
    lines.push('');
    for (const [i, idea] of (r.ideas || []).entries()) {
      lines.push(`### ${i + 1}. ${idea.title} ${idea.link_key ? `🔗(${idea.link_key})` : '📌価値提供'}`);
      lines.push('');
      lines.push(`- **フック（冒頭2秒）**: ${idea.hook}`);
      lines.push(`- **台本**: ${idea.script}`);
      if ((idea.scenes || []).length) {
        lines.push(`- **映像**:`);
        for (const s of idea.scenes) lines.push(`  - ${s}`);
      }
      lines.push(`- **CTA**: ${idea.cta}`);
      lines.push(`- **タグ**: ${(idea.hashtags || []).join(' ')}`);
      lines.push(`- **予測**: ${idea.engagement_prediction || '-'}`);
      lines.push('');
    }
  }
  if (complianceNotes.length) {
    lines.push('## コンプライアンスで破棄したネタ');
    lines.push('');
    for (const n of complianceNotes) lines.push(`- ${n}`);
    lines.push('');
  }
  const sources = [...new Set(results.flatMap((r) => r.sources || []))];
  if (sources.length) {
    lines.push('## 参照ソース');
    lines.push('');
    for (const s of sources) lines.push(`- ${s}`);
    lines.push('');
  }
  return lines.join('\n');
}

/** ジャンル選定レポートの Markdown */
function renderGenreMarkdown(date, data) {
  const lines = [`# 🎯 Shorts 第三弾 ジャンル選定リサーチ ${date}`, ''];
  lines.push('| ジャンル | 市場 | 競合 | 案件適合 | 制作 | 推薦度 |');
  lines.push('|---|---|---|---|---|---|');
  for (const c of data.candidates || []) {
    lines.push(`| ${c.genre} | ${c.market} | ${c.competition} | ${c.affiliate_fit} | ${c.production} | ${c.verdict} |`);
  }
  lines.push('');
  const rec = data.recommendation || {};
  lines.push(`## 推薦: ${rec.genre || '-'}`);
  lines.push('');
  lines.push(`**コンセプト**: ${rec.concept || '-'}`);
  lines.push('');
  lines.push(`**チャンネル名案**: ${(rec.channel_name_ideas || []).join(' / ')}`);
  lines.push('');
  lines.push(`**最初の1週間**: ${rec.first_week_direction || '-'}`);
  lines.push('');
  if ((data.sources || []).length) {
    lines.push('## 参照ソース');
    lines.push('');
    for (const s of data.sources) lines.push(`- ${s}`);
    lines.push('');
  }
  lines.push('---');
  lines.push('**採用手順**: config/youtube.json の第三弾チャンネルの genre / threads_genre を書き換え、開設後に status を active へ');
  lines.push('');
  return lines.join('\n');
}

/** engage.js と同じ方式で、1本の追跡 Issue にコメントとして配信する（スマホから確認できるように） */
async function postToTrackingIssue(body) {
  if (!GITHUB_TOKEN || !GITHUB_REPOSITORY) {
    console.log('  （GITHUB_TOKEN/GITHUB_REPOSITORY 未設定のためIssue投稿はスキップ）');
    return;
  }
  const headers = {
    Authorization: `token ${GITHUB_TOKEN}`,
    Accept: 'application/vnd.github.v3+json',
    'content-type': 'application/json'
  };
  const base = `https://api.github.com/repos/${GITHUB_REPOSITORY}`;

  const searchRes = await fetch(`${base}/issues?state=open&per_page=100`, { headers });
  const existing = await searchRes.json().catch(() => []);
  let issueNumber = Array.isArray(existing)
    ? (existing.find((i) => i.title === TRACKING_ISSUE_TITLE) || {}).number || null
    : null;

  if (!issueNumber) {
    const createRes = await fetch(`${base}/issues`, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        title: TRACKING_ISSUE_TITLE,
        labels: ['shorts-ideas'],
        body: '毎朝の Shorts 市場リサーチ&ネタ出しがコメントとして届きます。採用するネタを選び `node src/video-semi-auto.js --ideas` で動画化してください。'
      })
    });
    const created = await createRes.json().catch(() => ({}));
    if (!createRes.ok || !created.number) {
      console.log(`  ⚠️ Issue作成に失敗（${createRes.status}）`);
      return;
    }
    issueNumber = created.number;
    console.log(`  📌 追跡Issueを新規作成: #${issueNumber}`);
  }

  const commentRes = await fetch(`${base}/issues/${issueNumber}/comments`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ body })
  });
  if (!commentRes.ok) {
    console.log(`  ⚠️ Issueコメント投稿に失敗（${commentRes.status}）`);
  } else {
    console.log(`  📨 Issue #${issueNumber} にネタ出しキットを配信`);
  }
}

async function runGenreSelection(config) {
  console.log('🎯 第三弾ジャンル選定リサーチ開始\n');
  const response = await askClaude(buildGenreSelectionPrompt(config.channels || []), {
    system: SYSTEM_PROMPT,
    maxTokens: 8000,
    tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: 4 }]
  });
  const data = extractJSON(response);
  const date = todayJST();
  fs.mkdirSync(SHORTS_DIR, { recursive: true });
  const reportPath = path.join(SHORTS_DIR, `genre_research_${date}.md`);
  fs.writeFileSync(reportPath, renderGenreMarkdown(date, data), 'utf-8');
  console.log(`✅ 選定レポート: ${reportPath}`);
  const rec = (data.recommendation || {}).genre;
  if (rec) console.log(`   推薦ジャンル: ${rec}`);
  console.log('\n次のステップ: レポート確認 → config/youtube.json の第三弾チャンネルを更新');
}

async function runIdeas(config) {
  console.log('🎬 Shorts リサーチ&ネタ出し開始\n');
  const channels = (config.channels || []).filter((c) => c.status !== 'disabled');
  if (channels.length === 0) {
    console.error('❌ 対象チャンネルがありません（config/youtube.json を確認）');
    process.exit(1);
  }
  console.log(`  対象チャンネル: ${channels.map((c) => `${c.genre}(${c.status})`).join(', ')}`);
  const ideasPerChannel = config.ideas_per_channel || 5;

  // チャンネル別に分割生成（1チャンネルの失敗が他を巻き込まないよう個別に try/catch）
  const results = [];
  const complianceNotes = [];
  for (const channel of channels) {
    process.stdout.write(`  ${channel.genre} ... `);
    try {
      const response = await askClaude(
        buildChannelPrompt(
          channel,
          ideasPerChannel,
          buildThreadsSignal(channel.threads_genre),
          loadRecentTitles(channel.key)
        ),
        {
          system: SYSTEM_PROMPT,
          maxTokens: 8000,
          tools: [{ type: 'web_search_20250305', name: 'web_search', max_uses: 3 }]
        }
      );
      const r = extractJSON(response);
      r.status = channel.status;
      r.handle = channel.handle;

      // 台本・タイトル・CTA をまとめてコンプライアンス検査
      r.ideas = (r.ideas || []).filter((idea) => {
        const check = checkContent([idea.title, idea.hook, idea.script, idea.cta].filter(Boolean).join('\n'));
        if (!check.ok) {
          complianceNotes.push(`（${channel.genre}）${check.reasons.join(', ')}: ${String(idea.title).slice(0, 40)}`);
          return false;
        }
        return true;
      });
      results.push(r);
      console.log(`OK（ネタ ${r.ideas.length} 本）`);
    } catch (err) {
      console.log(`失敗（${err.message}）`);
      complianceNotes.push(`生成失敗（次回リトライ）: ${channel.genre}: ${err.message}`);
    }
  }
  if (results.length === 0) {
    console.error('❌ 全チャンネルの生成に失敗しました');
    process.exit(1);
  }

  const date = todayJST();
  fs.mkdirSync(SHORTS_DIR, { recursive: true });
  const reportPath = path.join(SHORTS_DIR, `ideas_${date}.md`);
  const markdown = renderIdeasMarkdown(date, results, complianceNotes);
  fs.writeFileSync(reportPath, markdown, 'utf-8');

  // 採用待ちネタ（video-semi-auto.js --ideas が読む）
  const allIdeas = results.flatMap((r) =>
    (r.ideas || []).map((idea) => ({ ...idea, channel: r.channel, genre: r.genre }))
  );
  writeJSON(PROPOSED_PATH, {
    generated_at: new Date().toISOString(),
    date,
    note: 'shorts-research.js によるネタ出し。採用分を node src/video-semi-auto.js --ideas で動画化',
    ideas: allIdeas
  });

  // 重複回避用の履歴に追記
  fs.mkdirSync(path.dirname(HISTORY_PATH), { recursive: true });
  for (const idea of allIdeas) {
    fs.appendFileSync(
      HISTORY_PATH,
      JSON.stringify({ date, channel: idea.channel, id: idea.id, title: idea.title }) + '\n',
      'utf-8'
    );
  }

  console.log(`\n✅ ネタ出しキット: ${reportPath}`);
  console.log(`✅ 採用待ちネタ: ${allIdeas.length}本（破棄 ${complianceNotes.length}件） → data/shorts_proposed_ideas.json`);

  await postToTrackingIssue(markdown);
  console.log('\n次のステップ: キット確認 → node src/video-semi-auto.js --ideas で採用分を動画化');
}

async function main() {
  const config = loadConfig('youtube', { channels: [] });
  if (process.argv.includes('--select-genre')) {
    await runGenreSelection(config);
  } else {
    await runIdeas(config);
  }
}

main().catch((err) => {
  console.error('\n🔴 エラー:', err.message);
  process.exit(1);
});
