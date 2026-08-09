#!/usr/bin/env node
'use strict';

/**
 * 動画ブリーフビルダー（マルチジャンル対応）
 *
 * config/briefs.json の1案件から、動画1本を作るのに必要なプロンプト一式を組み立てる。
 * ジャンル（スキンケア／ペット等）はブリーフの `domain` フィールドで切り替わり、
 * data/domains/<domain>/ 配下の viral-patterns.json・hooks.json・domain.json を読む。
 *
 *   ① Grok Imagine Agent Mode まるなげプロンプト（本命。計画→生成→スティッチ→仕上げまで一括）
 *   ② ChatGPT 画像生成プロンプト（Agent Mode に渡す被写体素材）
 *   ③ Grok Imagine 単体プロンプト（Agent Mode を使わない／特定シーンだけ作り直す時）
 *   ④ テロップ全文 ⑤ 投稿キャプション ⑥ コンプライアンス検査結果
 *
 * 設計方針:
 * - 型（バズの型）とジャンル固有コピー（domain.json）は data/domains/<domain>/ に外出しし、
 *   コードは組み立てに徹する。ジャンルを増やす＝ディレクトリを1つ足すだけ。コード変更は不要
 * - 生成物は必ず compliance.checkContent() を通す。モデルの賢さに品質を依存させない
 *   （CLAUDE.md 不変条件4と同じ思想）
 * - AI生成の被写体（人物／動物）は「世界観の担保」用途に限定し、状態変化の証拠には使わない。
 *   これは倫理の話であると同時に、景表法（優良誤認）・各ジャンルの表示規制の直撃を避けるための
 *   構造的な線引き。domain.json の forbidden_visuals / banned_claims_note がこの線を言語化する
 *
 * 使用方法:
 *   node src/build-brief.js --id orbis-u-01
 *   node src/build-brief.js --all
 *   node src/build-brief.js --list
 */

const fs = require('fs');
const path = require('path');
const { checkContent } = require('../../src/compliance');

const ROOT = path.join(__dirname, '..');
const DOMAINS_DIR = path.join(ROOT, 'data', 'domains');
const VARIANTS_PATH = path.join(ROOT, 'data', 'agent-variants.json');
const BRIEFS_PATH = process.env.BRIEFS_JSON || path.join(ROOT, 'config', 'briefs.json');
const OUT_DIR = path.join(ROOT, 'output');

const domainCache = new Map();

/** ジャンルごとの型・フック・固有コピーを読み込む（--all で同じジャンルが繰り返し出ても1回だけ読む） */
function loadDomain(domain) {
  if (domainCache.has(domain)) return domainCache.get(domain);
  const dir = path.join(DOMAINS_DIR, domain);
  if (!fs.existsSync(dir)) {
    throw new Error(`ジャンルが見つかりません: ${domain}（data/domains/${domain}/ が存在しない）`);
  }
  const data = {
    patterns: readJSON(path.join(dir, 'viral-patterns.json')),
    hooks: readJSON(path.join(dir, 'hooks.json')),
    config: readJSON(path.join(dir, 'domain.json'))
  };
  domainCache.set(domain, data);
  return data;
}

const PLATFORM_EXPORT = {
  instagram_reels: { res: '1080x1920', fps: 30, codec: 'H.264 High', bitrate: '12-16 Mbps (VBR 2pass)', audio: 'AAC 320kbps 48kHz', color: 'Rec.709 / sRGB', note: '90秒以内。フィード表示の上下約14%にUIが乗るため、テロップは中央60%に収める' },
  tiktok: { res: '1080x1920', fps: 30, codec: 'H.264 High', bitrate: '10-14 Mbps', audio: 'AAC 256-320kbps 48kHz', color: 'Rec.709 / sRGB', note: '再圧縮が強いので細いフォント・微細グラデは潰れる。テロップは太字・高コントラストで' },
  youtube_shorts: { res: '1080x1920', fps: 30, codec: 'H.264 High or HEVC', bitrate: '16-20 Mbps', audio: 'AAC 384kbps 48kHz', color: 'Rec.709', note: '60秒以内。YouTube側の再エンコードが最も素直なので高ビットレートを入れる価値がある' },
  threads: { res: '1080x1920', fps: 30, codec: 'H.264 High', bitrate: '10-14 Mbps', audio: 'AAC 256kbps 48kHz', color: 'Rec.709 / sRGB', note: '5分以内。Instagram と同じエンコードで使い回せる' }
};

function readJSON(p) {
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

function parseArgs(argv) {
  const args = { id: null, all: false, list: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--id') args.id = argv[++i];
    else if (argv[i] === '--all') args.all = true;
    else if (argv[i] === '--list') args.list = true;
  }
  return args;
}

/** {{key}} を values で置換する。未定義のキーは目立つ形で残し、記入漏れを検知できるようにする */
function fill(text, values) {
  return String(text).replace(/\{\{(\w+)\}\}/g, (_, key) => {
    const v = values[key];
    return v === undefined || v === '' ? `【要記入:${key}】` : v;
  });
}

function collectMissing(texts) {
  const missing = new Set();
  for (const t of texts) {
    for (const m of String(t).matchAll(/【要記入:(\w+)】/g)) missing.add(m[1]);
  }
  return [...missing];
}

/** 型とフックデータから、この案件の穴埋め値をまとめる */
function buildValues(brief, hooks) {
  const values = {
    concern: brief.concern || '肌の悩み',
    usp: brief.usp || '',
    product: brief.product || '',
    minutes: brief.minutes || '3',
    ...(brief.fill || {})
  };
  // hook_line 未指定なら、型に紐づくフォーミュラから決定論的に選ぶ
  // （日付やランダムで選ぶと同じブリーフから毎回違う台本が出て検証できなくなる）
  if (!values.hook_line) {
    const formula = brief.hook_formula || 'implied_result';
    const group = hooks.hooks.find((h) => h.formula === formula) || hooks.hooks[0];
    const idx = [...String(brief.id)].reduce((a, c) => a + c.charCodeAt(0), 0) % group.lines.length;
    values.hook_line = fill(group.lines[idx], values);
  }
  return values;
}

/** ChatGPT 画像生成用プロンプト（カットごと） */
function imagePrompts(pattern, persona, values, domainConfig) {
  const subject = domainConfig.subject_label;
  const base = [
    `同一${subject}・同一世界観で通すこと。${subject}設定: ${persona.age_look}、${persona.features}。`,
    `${persona.wardrobe ? `身なり: ${persona.wardrobe}。` : ''}場所: ${persona.location}。`,
    `${domainConfig.image_prompt_intro}`,
    `禁止: ${persona.forbidden}。`
  ].join('');

  return pattern.cuts.map((cut, i) => ({
    n: i + 1,
    t: cut.t,
    role: cut.role,
    prompt: `${base}\n【カット${i + 1}（${cut.role}）】${fill(cut.shot, values)}。この画像は静止画として完結させ、次の工程で動かす前提のため、被写体の輪郭がフレーム端で切れないようにする。`
  }));
}

/** Grok Imagine 画像→動画プロンプト（英語。動きの記述と「動かさないもの」を必ずセットで書く） */
function videoPrompts(pattern, values, domainConfig) {
  return pattern.cuts.map((cut, i) => {
    const [start, end] = cut.t.split('-').map(Number);
    const sec = Math.max(3, Math.min(10, Math.round(end - start)));
    const motion = fill(cut.motion, values);
    // 「静止」と書いてあるカットに Animate を素直に投げると、モデルが動きを捏造して
    // 被写体が崩れる。ほぼ静止であることを明示的に指示に翻訳する。
    const motionLine = /^静止/.test(motion)
      ? `Motion: near-static — ${motion}。Only micro-movements are allowed (breathing, a single blink, a subtle shift of light). Nothing else moves.`
      : `Motion: ${motion}. Keep the motion subtle and single-purpose — one clear movement only.`;
    return {
      n: i + 1,
      t: cut.t,
      sec,
      prompt: [
        `Animate this still photo. Subject: ${fill(cut.shot, values)}.`,
        motionLine,
        `Camera: hold the framing of the source image; no whip pans, no cuts inside the clip.`,
        `Must stay stable: ${domainConfig.stability_en}, and the product label must not change or morph at any point.`,
        `Mood: ${domainConfig.mood_en}.`,
        `Audio: ambient room tone only, no speech.`,
        `Duration: ${sec} seconds. 9:16 vertical.`
      ].join(' ')
    };
  });
}

/** テロップ全文 */
function captions(pattern, values) {
  return pattern.cuts.map((cut, i) => ({ n: i + 1, t: cut.t, text: fill(cut.caption, values) }));
}

/** 投稿キャプション（本文）。compliance を通す前提の素案 */
function postCaption(brief, pattern, values, domainConfig) {
  const lines = [
    fill(pattern.cuts[0].caption, values).replace(/^\(.*\)$/, ''),
    '',
    `${brief.product}｜${values.concern}が気になる時に。`,
    values.usp ? `・${values.usp}` : null,
    domainConfig.disclaimer_line,
    '',
    brief.ai_disclosure ? '※映像はAI生成です' : null,
    '#PR'
  ].filter((l) => l !== null);
  return lines.join('\n');
}

/** 型・フックの禁止語チェック（compliance.js の一般ルールに、ジャンル固有語を上乗せする） */
function contentLint(texts, banned) {
  const hits = [];
  for (const t of texts) {
    for (const word of banned) {
      if (String(t).includes(word)) hits.push({ word, text: t });
    }
  }
  return hits;
}

/**
 * ③ Grok Imagine Agent Mode への「まるなげ」プロンプト
 *
 * Agent Mode の実仕様に合わせた最適化ポイント（docs/market-research.md §5 参照）:
 * - 素材クリップの基本単位は6秒。シーン数は「尺 ÷ 6」ではなく、6秒素材を各シーンの
 *   目標尺にトリムして繋ぐ前提で書く。そうしないとエージェントが尺合わせに失敗する
 * - 日本語テロップはピクセルレベルで描画されるため文字化けする。焼き込ませず、
 *   セーフエリアを空けさせてテロップ台本をテキストで出させる
 * - ループ癖があるので「終端の状態を始端と変える」ことを明示する
 * - ストーリーボード承認を挟むかどうかを毎回明示する（黙っていると止まる）
 */
function agentModePrompt(brief, pattern, persona, values, caps, exportSpec, variant, domainConfig) {
  const subject = domainConfig.subject_label;
  const sceneTable = pattern.cuts.map((cut, i) => {
    const [s, e] = cut.t.split('-').map(Number);
    return `| ${i + 1} | ${(e - s).toFixed(1)}秒 | ${cut.role} | ${fill(cut.shot, values)} | ${fill(cut.motion, values)} |`;
  }).join('\n');

  const capTable = caps.map((c) => `| ${c.n} | ${c.t} | ${c.text} |`).join('\n');

  return `あなたはプロのアフィリエイト動画ディレクター兼UGCクリエイターです。
Grok Imagine Agent Mode として、以下をすべて活用し、視聴維持率が高くクリックしたくなる縦型アフィリエイト動画を、まるなげで最後まで完成させてください。

【やること】
1. 下の構成表をもとに ${pattern.cuts.length} シーンのストーリーボードを確定する
2. 同一人物・同一商品を保ったまま各シーンを生成する（素材は6秒で作り、目標尺にトリムする）
3. スティッチして1本に繋ぐ
4. 効果音・BGM・CTAを配置する
5. 完成動画と、後述の納品物一式を出力する

【動画の条件】
- 形式: 9:16 縦型（${brief.platform}）
- 尺: ${pattern.duration_sec}秒
- トーン: ${brief.tone || '自然なUGC風。広告然としない、生活の中で撮られた感じ'}
- ターゲット: ${values.concern}が気になっている${brief.target || '20代後半〜30代前半'}
- 採用する型: ${pattern.name}
  （${pattern.why}）

【商品情報】
- 商品名: ${brief.product}（${brief.category}）
- 狙う悩み: ${values.concern}
- 主な特徴・訴求: ${values.usp || '【要記入:usp】'}
- CTA文言: ${caps[caps.length - 1].text}

【${subject} — 全シーンで固定】
${persona.age_look}、${persona.features}。${persona.wardrobe ? `身なり: ${persona.wardrobe}。` : ''}場所: ${persona.location}。
アップロードした${subject}画像を厳密に参照し、シーンをまたいで${domainConfig.stability_ja}が変化しないようにしてください。
変化したシーンは採用せず、生成し直してください。

【シーン構成 — この順序と尺を守る】
| # | 目標尺 | 役割 | 画（何が映るか） | 動き |
|---|---|---|---|---|
${sceneTable}

【生成時のルール】
- 1シーンにつき動きは1種類だけ。複数の動きを重ねると破綻します
- カメラは1シーン内でフレーミングを保持。シーンの内側でカットを割らないでください
- 目標尺が3秒を超えるシーンは、カットを割らずに、ゆっくりした寄り／引きで内部に変化を作ってください（動きが一定だと3秒目から離脱します）
- **ループ回避**: 各シーンは終端の状態を始端と変えてください（同じ位置に戻すとループに見えます）
- ${domainConfig.stability_ja}・商品ラベルは一切変形させないでください
- 商品の見た目・色・ロゴは、アップロードした商品画像どおりに正確に保ってください
- ${subject}にセリフを喋らせないでください。音声は環境音とBGMのみ
- 0〜2秒に商品名・ロゴを出さないでください（広告と判定されて離脱します）

【テロップの扱い — 重要】
動画内に日本語の文字を焼き込まないでください。文字が崩れます。
代わりに、以下2点を守ってください。
1. 全シーンで、画面**上15%と下25%を無地に近い状態**に保つ（後からテロップを乗せるセーフエリア）
2. テロップ文言は焼き込まず、納品物④としてタイムコード付きのテキストで出力する
英数字の短い表記（商品名の英字ロゴなど）だけは、商品画像に写っているものをそのまま保つ形で可とします。

想定しているテロップ（この文言をタイムコードに割り当てて④として出力してください）:
| # | タイムコード | テロップ |
|---|---|---|
${capTable}

【音】
${pattern.audio}
シーンの切り替わりに合わせてSFXを置き、5秒に1回は音か画に変化を作ってください（パターンインタラプト）。

【書き出し】
${exportSpec.res} / ${exportSpec.fps}fps / ${exportSpec.codec} / ${exportSpec.bitrate} / 音声 ${exportSpec.audio} / ${exportSpec.color}
${exportSpec.note}

【守ること — 違反したシーンは採用しない】
- 効果・効能を断定しないでください。${domainConfig.banned_claims_note}
- ${domainConfig.forbidden_visuals}
- 架空の${subject}に一人称の体験談・使用感を語らせないでください
- 実在の人物・ブランド・キャラクターに似せないでください
- 露出の高い服装、扇情的なポーズにしないでください
${brief.ai_disclosure ? '- 最終シーンに「AI生成」の旨を表示できる無地の余白を残してください' : ''}
- 「絶対」「必ず」「100%」などの断定強調を使わないでください

【進め方】
まずストーリーボードを提示してください。私が承認したら、生成・スティッチ・仕上げまで止まらずに実行してください。

【納品物】
1. 完成動画（${pattern.duration_sec}秒 / 9:16）
2. 使用したシーンごとの生成プロンプト
3. 編集判断の一覧（タイムコード / 編集アクション / ビジュアル / 音声・SFX / メモ の5列の表）
4. テロップ台本（タイムコード付きテキスト。動画には焼き込まない）
5. 上の「守ること」への自己チェック結果（各項目 OK/NG と根拠）${variant ? `\n\n【追加指示（${variant.name}）】\n${variant.add}` : ''}`;
}

function render(brief, cfg, variants) {
  const domain = brief.domain || 'skincare';
  const { patterns, hooks, config: domainConfig } = loadDomain(domain);
  const pattern = patterns.patterns.find((p) => p.id === brief.pattern_id);
  if (!pattern) throw new Error(`型が見つかりません: ${brief.pattern_id}（domain: ${domain}）`);
  const personas = cfg.personas || (cfg.persona ? { skincare: cfg.persona } : {});
  const persona = brief.persona || personas[domain];
  if (!persona) throw new Error(`ペルソナが見つかりません。config/briefs.json の personas.${domain} を定義してください`);
  const values = buildValues(brief, hooks);
  const exportSpec = PLATFORM_EXPORT[brief.platform] || PLATFORM_EXPORT.instagram_reels;

  const imgs = imagePrompts(pattern, persona, values, domainConfig);
  const vids = videoPrompts(pattern, values, domainConfig);
  const caps = captions(pattern, values);
  const caption = postCaption(brief, pattern, values, domainConfig);
  const variant = brief.variant ? (variants.variants || {})[brief.variant] : null;
  if (brief.variant && !variant) throw new Error(`variant が見つかりません: ${brief.variant}`);
  const agentPrompt = agentModePrompt(brief, pattern, persona, values, caps, exportSpec, variant, domainConfig);

  // 検品
  const captionCheck = checkContent(caption);
  // 検品対象は「視聴者の目に触れるもの」だけ。agentPrompt は禁止語を禁止語として列挙して
  // いるため、ここに含めると必ず自己ヒットする。
  const lintTargets = [...caps.map((c) => c.text), caption];
  const lintHits = contentLint(lintTargets, hooks.banned_in_hooks);
  const missing = collectMissing([...caps.map((c) => c.text), ...imgs.map((i) => i.prompt), agentPrompt]);

  const subject = domainConfig.subject_label;
  const md = `# 動画ブリーフ: ${brief.id}

- ジャンル: **${domain}**
- 商品: **${brief.product}**（${brief.category}）
- 悩み: ${values.concern} / 訴求: ${values.usp || '（未設定）'}
- 型: **${pattern.name}**（\`${pattern.id}\` / ${pattern.tier}ランク）
- 尺: ${pattern.duration_sec}秒 / 必要画像: ${pattern.cuts.length}枚 / 配信先: ${brief.platform}
- link_key: \`${brief.link_key}\`

> なぜこの型か: ${pattern.why}

---

## ① Grok Imagine Agent Mode まるなげプロンプト ← 本命

**手順**: grok.com/imagine（デスクトップ）→ Agent Mode を ON → プリセット **UGC Product Stories** を選択
→ ${subject}画像（②で作ったもの）と商品写真をアップロード → 以下を貼って送信 → ストーリーボードを承認。

${variant ? `適用バリアント: **${variant.name}**（\`${brief.variant}\`）\n` : ''}
\`\`\`
${agentPrompt}
\`\`\`

---

## ② ChatGPT 画像生成プロンプト（Agent Modeに渡す素材）

先に \`prompts/character-sheet.md\` でベース画像を1枚作り、**そのベース画像を毎回添付した上で**以下を投げる。
テキストだけで同一${subject}を出そうとすると必ず特徴が変わる。
Agent Mode に渡すのは${subject}カットだけでよい（商品カットは実物の商品写真を使う方が正確）。

${imgs.map((p) => `### カット${p.n}（${p.t} ${p.role}）\n\`\`\`\n${p.prompt}\n\`\`\``).join('\n\n')}

---

## ③ Grok Imagine 単体プロンプト（フォールバック）

Agent Mode を使わない場合、またはAgent Modeの出力が破綻した特定シーンだけ作り直す場合に使う。
各カットの画像をアップロードして以下を貼る。1クリップ最大10秒（Imagine 1.0、基本単位は6秒）。
被写体と動きの記述は編集しやすいよう日本語のまま残してある。指示追従が弱い時は英訳する。
動きが出ない場合は「Motion:」の動詞を強い語（drifts / unfurls / surges）に差し替える。

${vids.map((p) => `### カット${p.n}（${p.t} / ${p.sec}秒）\n\`\`\`\n${p.prompt}\n\`\`\``).join('\n\n')}

---

## ④ テロップ全文

| # | タイムコード | テロップ |
|---|---|---|
${caps.map((c) => `| ${c.n} | ${c.t} | ${c.text} |`).join('\n')}

## ⑤ 投稿キャプション

\`\`\`
${captionCheck.text}
\`\`\`

## ⑥ 検品結果

- compliance.checkContent: **${captionCheck.ok ? 'PASS' : 'BLOCK'}**${captionCheck.reasons.length ? `（${captionCheck.reasons.join(' / ')}）` : ''}
- ${domainConfig.banned_word_label}: ${lintHits.length === 0 ? '**なし**' : `**${lintHits.length}件** → ${lintHits.map((h) => `「${h.word}」`).join(' ')}`}
- 記入漏れ: ${missing.length === 0 ? '**なし**' : `**${missing.join(', ')}** を briefs.json の \`fill\` に追加すること`}
- 型の固有リスク: ${pattern.risk_notes}
- AIラベル: ${brief.ai_disclosure ? '**必要**（投稿時にプラットフォームのAI表示をONにする）' : '不要'}

## ⑦ 仕上げ

Agent Mode は日本語テロップを焼き込めないので、①の納品物④として出てくるテロップ台本を
自分で乗せる。上下のセーフエリア（上15% / 下25%）を空けさせてあるのでそこに置く。
出しきれない時の追い込み方は \`prompts/grok-agent-mode.md\` の「詰まった時」を参照。
投稿前に \`docs/compliance-checklist.md\` を1回通すこと。
`;

  return { md, ok: captionCheck.ok && lintHits.length === 0, missing, lintHits };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const variants = readJSON(VARIANTS_PATH);
  const cfg = readJSON(BRIEFS_PATH);

  if (args.list) {
    const domains = [...new Set(cfg.briefs.map((b) => b.domain || 'skincare'))];
    for (const domain of domains) {
      const { patterns } = loadDomain(domain);
      console.log(`--- 型（${domain}） ---`);
      for (const p of patterns.patterns) console.log(`  ${p.tier}  ${p.id.padEnd(28)} ${p.name}（${p.duration_sec}秒 / 画像${p.cuts.length}枚）`);
    }
    console.log('--- ブリーフ ---');
    for (const b of cfg.briefs) console.log(`     [${(b.domain || 'skincare').padEnd(9)}] ${b.id.padEnd(20)} ${b.product} / ${b.pattern_id}`);
    return;
  }

  const targets = args.all ? cfg.briefs : cfg.briefs.filter((b) => b.id === args.id);
  if (targets.length === 0) {
    console.error(`ブリーフが見つかりません。--list で一覧を確認してください（--id / --all）`);
    process.exit(1);
  }

  fs.mkdirSync(OUT_DIR, { recursive: true });
  let failed = 0;
  for (const brief of targets) {
    const { md, ok, missing, lintHits } = render(brief, cfg, variants);
    const out = path.join(OUT_DIR, `${brief.id}.md`);
    fs.writeFileSync(out, md);
    const status = ok ? 'OK' : 'REQUIRES FIX';
    console.log(`[${status}] ${out}`);
    if (missing.length) console.log(`         記入漏れ: ${missing.join(', ')}`);
    if (lintHits.length) console.log(`         禁止語: ${lintHits.map((h) => h.word).join(', ')}`);
    if (!ok) failed++;
  }
  if (failed > 0) process.exit(2);
}

if (require.main === module) main();

module.exports = { render, fill, videoPrompts, imagePrompts, agentModePrompt, contentLint, loadDomain, PLATFORM_EXPORT };
