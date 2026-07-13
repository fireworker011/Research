#!/usr/bin/env node
'use strict';

/**
 * Engagement Kit（毎朝の「コピペ10分」用の素材を全自動生成）
 *
 * やること:
 * 1. 各アカウントの直近投稿への未対応リプを Threads API で収集
 * 2. ジャンルごとのキーワード検索（threads_keyword_search 権限があれば）で
 *    今日コメントを付けに行く先の候補投稿を収集
 * 3. Claude がアカウントのペルソナに合わせた返信文・コメント文の下書きを生成
 * 4. output/engage/engage_YYYY-MM-DD.md に「今日の10分ルーチン」としてまとめる
 *
 * やらないこと（設計判断）:
 * - リプ・いいね・フォローの自動実行はしない。
 *   いいね/フォローはそもそも公式 Threads API に存在せず、非公式自動化は
 *   Meta 規約違反で凍結リスクが最も高い行為。返信の自動送信も「人間を装う
 *   ボット」となるため行わない。ここは唯一、人間が1日10分だけ手を動かす場所であり、
 *   下書きは全部この仕組みが用意する。
 *
 * 使用方法:
 *   ANTHROPIC_API_KEY=... node src/engage.js
 */

const fs = require('fs');
const path = require('path');
const { askClaude, extractJSON } = require('./claude-client');
const { OUTPUT_DIR, loadConfig, todayJST } = require('./util');

const THREADS_API = 'https://graph.threads.net/v1.0';
const REPLY_LOOKBACK_HOURS = parseFloat(process.env.REPLY_LOOKBACK_HOURS || '72');

const GITHUB_TOKEN = process.env.GITHUB_TOKEN || '';
const GITHUB_REPOSITORY = process.env.GITHUB_REPOSITORY || '';
const TRACKING_ISSUE_TITLE = '📋 デイリー・エンゲージメントキット';

/** スマホでも読めるよう、GitHub Issueへコメントとして毎日投稿する（新規Issue量産を避けるため1本のIssueに追記していく） */
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

  // タイトル一致で既存Issueを探す（ラベルは環境により付与されないことがあるため頼らない）
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
        labels: ['daily-engage'],
        body: 'このIssueに、毎日06:00JSTのエンゲージメントキット（返信・コメント下書き）がコメントとして追加されます。スマホのGitHub通知から確認してください。'
      })
    });
    const created = await createRes.json().catch(() => ({}));
    if (!createRes.ok) {
      console.warn(`  ⚠️ 追跡Issueの作成に失敗: ${createRes.status}`);
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
    console.warn(`  ⚠️ Issueコメント投稿に失敗: ${commentRes.status}`);
    return;
  }
  const comment = await commentRes.json().catch(() => ({}));
  console.log(`  ✅ Issueにコメント投稿: ${comment.html_url || `#${issueNumber}`}`);
}

/** アカウントごとの返信・コメントのトーン（ペルソナ） */
const PERSONAS = {
  konkatsu: '婚活情報を整理して発信する30代女性。共感ファースト、押し付けない、絵文字は控えめ',
  sidejob: '数字に慎重で誠実な30代会社員男性。盛らない、断定しない、失敗談に寛容',
  beauty: '仕事と家のことで手一杯な30代後半女性。ゆるい、やさしい、頑張らせない',
  bodymake: '週2×30分だけジムに行くデスクワーカー。軽妙、ストイックさを求めない',
  education: '小学生の子を持つ保護者。丁寧、焦らせない、家庭ごとの事情を尊重',
  setsuyaku: '我慢する節約をやめた30代。実利主義だが説教しない、仕組み好き',
  tenshoku: '転職を煽らないキャリア整理役。冷静、データ好き、「残る選択」も尊重',
  pet: '犬と暮らす飼い主。あたたかい、心配性の飼い主に寄り添う、安全側に倒す',
  sleep: '眠りを整えることに詳しい30代。落ち着いた夜のトーン、頑張らせない、断定しない'
};

/** ジャンルごとのコメント回り検索キーワード */
const SEARCH_KEYWORDS = {
  婚活: ['婚活', 'マッチングアプリ 疲れた'],
  副業: ['副業 会社員', '副業 始め方'],
  美容: ['スキンケア 時短', '乾燥肌'],
  筋トレ: ['筋トレ 続かない', 'ジム 初心者'],
  教育: ['習い事 小学生', 'プログラミング教育'],
  節約: ['節約 固定費', '家計簿 続かない'],
  転職: ['転職 迷う', '仕事 辞めたい'],
  ペット: ['犬 留守番', '子犬 しつけ'],
  睡眠: ['眠れない', '睡眠 改善']
};

async function threadsGet(endpoint, params) {
  const url = new URL(`${THREADS_API}${endpoint}`);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }
  const res = await fetch(url);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(`Threads API ${res.status}: ${data.error?.message || JSON.stringify(data)}`);
  }
  return data;
}

/** 1アカウント分: 未対応リプの収集 */
async function collectReplies(account) {
  const { userId, token } = account;
  const me = await threadsGet(`/${userId}`, { fields: 'username', access_token: token });
  const ownUsername = me.username;

  // 自分の返信済み一覧（対応済み判定用）。権限や仕様差で失敗したら空扱い
  const answeredIds = new Set();
  try {
    const myReplies = await threadsGet(`/${userId}/replies`, {
      fields: 'replied_to',
      limit: '50',
      access_token: token
    });
    for (const r of myReplies.data || []) {
      if (r.replied_to?.id) answeredIds.add(r.replied_to.id);
    }
  } catch (_) {
    // 判定不能でも下書きは出す（レポートに注記）
  }

  const posts = await threadsGet(`/${userId}/threads`, {
    fields: 'id,text,permalink,timestamp',
    limit: '10',
    access_token: token
  });

  const cutoff = Date.now() - REPLY_LOOKBACK_HOURS * 3600 * 1000;
  const pending = [];
  for (const post of posts.data || []) {
    let replies;
    try {
      replies = await threadsGet(`/${post.id}/replies`, {
        fields: 'id,text,username,timestamp,permalink',
        access_token: token
      });
    } catch (_) {
      continue;
    }
    for (const reply of replies.data || []) {
      if (reply.username === ownUsername) continue;
      if (answeredIds.has(reply.id)) continue;
      if (reply.timestamp && new Date(reply.timestamp).getTime() < cutoff) continue;
      pending.push({
        reply_id: reply.id,
        from: reply.username,
        text: reply.text || '',
        post_excerpt: (post.text || '').slice(0, 80),
        permalink: reply.permalink || post.permalink || ''
      });
    }
  }
  return { ownUsername, pending };
}

/** 1ジャンル分: コメント回り先の候補投稿（キーワード検索 API・権限がなければ空） */
async function searchMarketPosts(genre, token) {
  const keywords = SEARCH_KEYWORDS[genre] || [genre];
  const results = [];
  for (const q of keywords.slice(0, 2)) {
    try {
      const found = await threadsGet('/keyword_search', {
        q,
        search_type: 'TOP',
        fields: 'id,text,username,permalink',
        access_token: token
      });
      for (const p of (found.data || []).slice(0, 4)) {
        results.push({
          keyword: q,
          username: p.username,
          text: (p.text || '').slice(0, 200),
          permalink: p.permalink || ''
        });
      }
    } catch (err) {
      return { error: err.message, results: [] };
    }
  }
  return { error: null, results };
}

function buildPrompt(payload) {
  return `Threads 運用アカウント群の「今日のエンゲージメント素材」を作成してください。

【アカウントとペルソナ】
${JSON.stringify(payload.personas, null, 1)}

【未対応リプ一覧】
${JSON.stringify(payload.replies, null, 1)}

【コメント回り先の候補投稿（ジャンル別・市場の実投稿）】
${JSON.stringify(payload.market, null, 1)}

【タスク】
1. 未対応リプそれぞれに、そのアカウントのペルソナに合った返信下書きを1本作る。
   - 相手の発言内容に具体的に触れる。テンプレ感を出さない。長さは1〜3文でばらつかせる
   - 商品・リンクへの誘導はしない。会話を1往復続けられる軽い問い返しを時々入れる
2. コメント回り先の候補投稿それぞれに、そのジャンル担当アカウントとして付けるコメント下書きを1本作る。
   - 相手の投稿への具体的な反応・共感・ちょい足し情報。宣伝・誘導・定型文は禁止
3. 出力は以下の JSON のみ:
{
  "reply_drafts": [
    { "account": "アカウントkey", "reply_id": "元リプID", "from": "相手ユーザー名", "draft": "返信下書き" }
  ],
  "comment_drafts": [
    { "account": "アカウントkey", "genre": "ジャンル", "target_username": "相手", "target_permalink": "URL", "draft": "コメント下書き" }
  ]
}

【禁止事項】使ってもいない商品の体験談の捏造、誇大表現、医療・効果効能の断定、収益の断定、他者への攻撃的表現`;
}

const SYSTEM_PROMPT = `あなたは日本のSNSコミュニティマネージャーです。
自然で感じの良い日本語の返信・コメントを書きます。営業感・テンプレ感を出さず、
文体・長さ・絵文字の使い方を投稿ごとに変えます。出力は指示された JSON のみ。`;

function renderMarkdown(date, drafts, replyMeta, marketMeta, notes) {
  const lines = [
    `# エンゲージメント・キット ${date}`,
    '',
    '**使い方（1日10分）**: 下書きをそのまま or 軽く直してアプリから返信・コメントする。',
    'いいねは返信・コメントしたついでに周辺の投稿へ 10〜20 件。フォローは「2回以上絡んだ相手」だけに絞る。',
    '自動送信はしない設計（凍結リスクと信頼のため）。ここだけが人間の仕事です。',
    ''
  ];

  lines.push('## 1. 未対応リプへの返信下書き');
  lines.push('');
  if ((drafts.reply_drafts || []).length === 0) {
    lines.push('（対応が必要なリプはありません）');
  } else {
    for (const d of drafts.reply_drafts) {
      const meta = replyMeta.find((r) => r.reply_id === d.reply_id) || {};
      lines.push(`### @${d.from} への返信（${d.account}）`);
      if (meta.permalink) lines.push(`- 場所: ${meta.permalink}`);
      if (meta.text) lines.push(`- 相手のリプ: ${meta.text}`);
      lines.push('```');
      lines.push(d.draft || '');
      lines.push('```');
      lines.push('');
    }
  }

  lines.push('## 2. コメント回り（市場の投稿に価値あるコメントを付けに行く）');
  lines.push('');
  if ((drafts.comment_drafts || []).length === 0) {
    lines.push('（本日は候補なし）');
  } else {
    for (const d of drafts.comment_drafts) {
      lines.push(`### @${d.target_username} の投稿へ（${d.account} / ${d.genre}）`);
      if (d.target_permalink) lines.push(`- 場所: ${d.target_permalink}`);
      lines.push('```');
      lines.push(d.draft || '');
      lines.push('```');
      lines.push('');
    }
  }

  if (notes.length) {
    lines.push('## 注記');
    lines.push('');
    for (const n of notes) lines.push(`- ${n}`);
    lines.push('');
  }
  return lines.join('\n');
}

async function main() {
  console.log('🤝 Engagement Kit 生成開始\n');
  const date = todayJST();
  const accountsConfig = loadConfig('accounts', { accounts: [] });
  const notes = [];

  const accounts = accountsConfig.accounts
    .filter((a) => a.enabled !== false)
    .map((a) => ({ ...a, userId: process.env[a.user_id_env], token: process.env[a.token_env] }));

  const withCreds = accounts.filter((a) => a.userId && a.token);
  for (const a of accounts.filter((x) => !x.userId || !x.token)) {
    notes.push(`${a.key}: トークン未設定のためスキップ（Secrets に ${a.user_id_env} / ${a.token_env} を登録すると対象になる）`);
  }

  const allReplies = [];
  const market = {};
  for (const account of withCreds) {
    try {
      const { pending } = await collectReplies(account);
      console.log(`  ${account.key}: 未対応リプ ${pending.length} 件`);
      for (const p of pending) allReplies.push({ account: account.key, ...p });
    } catch (err) {
      notes.push(`${account.key}: リプ収集に失敗（${err.message}）`);
    }

    if (!market[account.genre]) {
      const res = await searchMarketPosts(account.genre, account.token);
      if (res.error) {
        notes.push(`${account.genre}: キーワード検索が利用できません（threads_keyword_search 権限の追加で有効化）`);
      }
      market[account.genre] = res.results;
    }
  }

  const marketFlat = Object.entries(market).flatMap(([genre, posts]) =>
    posts.map((p) => ({
      genre,
      account: (withCreds.find((a) => a.genre === genre) || {}).key,
      ...p
    }))
  );

  let drafts = { reply_drafts: [], comment_drafts: [] };
  if (allReplies.length > 0 || marketFlat.length > 0) {
    const personas = Object.fromEntries(
      withCreds.map((a) => [a.key, `${a.genre} / ${PERSONAS[a.key] || '自然で丁寧'}`])
    );
    // 返信・コメントの下書きは軽量モデルで十分（コスト: config/budget.json で変更可）
    const budget = loadConfig('budget', {});
    const response = await askClaude(
      buildPrompt({ personas, replies: allReplies, market: marketFlat }),
      {
        system: SYSTEM_PROMPT,
        maxTokens: 8192,
        model: budget.engage_model || 'claude-haiku-4-5-20251001'
      }
    );
    drafts = extractJSON(response);
  } else if (withCreds.length > 0) {
    notes.push('未対応リプ・コメント回り候補ともに0件でした（開設初期は正常です）');
  }

  const markdown = renderMarkdown(date, drafts, allReplies, marketFlat, notes);

  const engageDir = path.join(OUTPUT_DIR, 'engage');
  fs.mkdirSync(engageDir, { recursive: true });
  const outPath = path.join(engageDir, `engage_${date}.md`);
  fs.writeFileSync(outPath, markdown, 'utf-8');

  console.log(`\n✅ ${outPath}`);
  console.log(`   返信下書き ${(drafts.reply_drafts || []).length} 本 / コメント下書き ${(drafts.comment_drafts || []).length} 本`);

  await postToTrackingIssue(markdown);
}

main().catch((err) => {
  console.error('\n🔴 エラー:', err.message);
  process.exit(1);
});
