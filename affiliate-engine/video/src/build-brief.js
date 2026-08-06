#!/usr/bin/env node
'use strict';

/**
 * スキンケア動画ブリーフビルダー
 *
 * config/briefs.json の1案件から、動画1本を作るのに必要なプロンプト一式を組み立てる。
 *
 *   ① ChatGPT 画像生成プロンプト（キャラ固定＋カットごとの差分）
 *   ② Grok Imagine 画像→動画プロンプト（カットごと）
 *   ③ imagine agent 丸投げプロンプト（①②＋編集指示の「がっちゃんこ」）
 *   ④ Gemini 編集プロンプト（案件で穴埋め済み）
 *   ⑤ キャプション・テロップ＋コンプライアンス検査結果
 *
 * 設計方針:
 * - 型（バズの型）は data/viral-patterns.json に外出しし、コードは組み立てに徹する。
 *   型を増やす＝JSONを足すだけ。コード変更を伴わない。
 * - 生成物は必ず compliance.checkContent() を通す。モデルの賢さに品質を依存させない
 *   （CLAUDE.md 不変条件4と同じ思想）。
 * - AI美女画像は「世界観の担保」用途に限定し、肌の変化の証拠には使わない。
 *   これは倫理の話であると同時に、景表法（優良誤認）・薬機法の直撃を避けるための構造的な線引き。
 *
 * 使用方法:
 *   node src/build-brief.js --id 2026-08-serum-a
 *   node src/build-brief.js --all
 *   node src/build-brief.js --list
 */

const fs = require('fs');
const path = require('path');
const { checkContent } = require('../../src/compliance');

const ROOT = path.join(__dirname, '..');
const PATTERNS_PATH = path.join(ROOT, 'data', 'viral-patterns.json');
const HOOKS_PATH = path.join(ROOT, 'data', 'hooks.json');
const BRIEFS_PATH = process.env.BRIEFS_JSON || path.join(ROOT, 'config', 'briefs.json');
const OUT_DIR = path.join(ROOT, 'output');

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
function imagePrompts(pattern, persona, values) {
  const base = [
    `同一人物・同一世界観で通すこと。人物設定: ${persona.age_look}、${persona.features}。`,
    `衣装: ${persona.wardrobe}。場所: ${persona.location}。`,
    '写真的リアリズム、自然光、9:16縦構図、被写界深度浅め、加工しすぎない肌質（毛穴とうぶ毛を残す）。',
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
function videoPrompts(pattern, values) {
  return pattern.cuts.map((cut, i) => {
    const [start, end] = cut.t.split('-').map(Number);
    const sec = Math.max(3, Math.min(10, Math.round(end - start)));
    const motion = fill(cut.motion, values);
    // 「静止」と書いてあるカットに Animate を素直に投げると、モデルが動きを捏造して
    // 顔が溶ける。ほぼ静止であることを明示的に指示に翻訳する。
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
        `Must stay stable: the person's facial structure, hairstyle, skin tone, clothing, and the product label must not change or morph at any point.`,
        `Mood: calm, natural daylight, soft contrast, editorial skincare commercial.`,
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
function postCaption(brief, pattern, values) {
  const lines = [
    fill(pattern.cuts[0].caption, values).replace(/^\(.*\)$/, ''),
    '',
    `${brief.product}｜${values.concern}が気になる日に。`,
    values.usp ? `・${values.usp}` : null,
    '・個人差があります。パッチテストをしてから使ってください',
    '',
    brief.ai_disclosure ? '※映像はAI生成です' : null,
    '#PR'
  ].filter((l) => l !== null);
  return lines.join('\n');
}

/** 型・フックの禁止語チェック（compliance.js の一般ルールに、スキンケア固有語を上乗せする） */
function skincareLint(texts, banned) {
  const hits = [];
  for (const t of texts) {
    for (const word of banned) {
      if (String(t).includes(word)) hits.push({ word, text: t });
    }
  }
  return hits;
}

/** ③ imagine agent への丸投げプロンプト（画像→動画 ＋ 編集 の「がっちゃんこ」） */
function imagineAgentPrompt(brief, pattern, persona, values, vids, caps, exportSpec) {
  const cutTable = pattern.cuts.map((cut, i) =>
    `| ${i + 1} | ${cut.t} | ${cut.role} | ${fill(cut.shot, values)} | ${fill(cut.motion, values)} | ${fill(cut.caption, values)} |`
  ).join('\n');

  return `あなたは、静止画から縦型ショート動画を1本完成させる映像ディレクター兼エディターです。
YouTube・ドキュメンタリー編集で15年以上の経験を持つシニアエディターとして振る舞ってください。
入力として、同一人物・同一世界観のAI生成静止画を ${pattern.cuts.length} 枚渡します。
これらを「画像→動画化」し、続けて「1本の動画への編集」まで、途中で私に確認を取らず最後まで実行してください。

## 案件
- 商品: ${brief.product}（${brief.category}）
- 狙う悩み: ${values.concern}
- 訴求: ${values.usp || '【要記入:usp】'}
- 尺: ${pattern.duration_sec}秒 / 9:16 / 配信先: ${brief.platform}
- 採用する型: ${pattern.name}（${pattern.why}）

## 登場人物（全カットで固定）
${persona.age_look}、${persona.features}。衣装: ${persona.wardrobe}。場所: ${persona.location}。
カットをまたいで顔・髪型・肌の色・衣装が変化してはいけません。変化したカットは破棄して作り直してください。

## 第1工程：画像→動画（各カットを個別に生成）
各カットについて、以下の要件を満たす動画クリップを作ってください。
- 動きは1カットにつき1種類だけ。複数の動きを重ねると破綻します
- カメラは元画像のフレーミングを保持。クリップ内でカットを割らない
- 顔の構造・髪型・肌の色・衣装・商品ラベルは一切変形させない
- 音声は環境音のみ。人物にセリフを喋らせない

| # | タイムコード | 役割 | 画（何が映るか） | 動き | テロップ |
|---|---|---|---|---|---|
${cutTable}

各カットの生成プロンプト（そのまま使用可）:
${vids.map((v) => `- カット${v.n}（${v.sec}秒）: ${v.prompt}`).join('\n')}

## 第2工程：編集（1本に組み上げる）
第1工程のクリップを、上の表のタイムコード順に接続し、次を適用してください。
1. **冒頭0-2秒**: 視覚フックとテロップを同時に立てる。商品名・ロゴはこの区間に出さない
2. **カット尺**: 平均1.2〜2.5秒。3秒を超えるカットは中で寄り／引きを作って変化を入れる
3. **テロップ**: 太字・高コントラスト・画面中央60%以内（上下のUIに隠れるため）。1カット1メッセージ
4. **音**: ${pattern.audio}
5. **トランジション**: 基本はストレートカット。使う場合もホイップパン/フラッシュを全体で1回まで
6. **パターンインタラプト**: 5秒に1回、SFX・ズーム・テロップ切替のいずれかで変化を作る
7. **CTA**: 最終カットに「${caps[caps.length - 1].text}」を出す
8. **書き出し**: ${exportSpec.res} / ${exportSpec.fps}fps / ${exportSpec.codec} / ${exportSpec.bitrate} / 音声 ${exportSpec.audio} / ${exportSpec.color}。${exportSpec.note}

## 守ること（違反したら作り直し）
- 効果・効能を断定しない。化粧品の効能効果の範囲を超える表現（「シミが消える」「ニキビが治る」「美白になる」等）を映像・音声・テロップのいずれにも入れない
- 使用前後の変化を見せない／示唆する画作りをしない。この人物の肌は「成果」ではなく「世界観」です
- 架空の人物に体験談を語らせない。一人称の使用感を音声・テロップで語らせない
- 実在の人物・ブランドに似せない
${brief.ai_disclosure ? '- 最終カットに「AI生成」の旨を表示する（映像内表示＋投稿時のAIラベル両方）' : ''}
- 広告表記 #PR をキャプションに必ず含める

## 出力
1. 完成動画（${pattern.duration_sec}秒、9:16）
2. 使用した編集判断の一覧（タイムコード / 編集アクション / B-roll・ビジュアル / 音声・SFX / 編集メモ の5列の表）
3. 上の「守ること」への自己チェック結果（各項目 OK/NG と根拠）`;
}

function render(brief, patterns, hooks, personaDefault) {
  const pattern = patterns.patterns.find((p) => p.id === brief.pattern_id);
  if (!pattern) throw new Error(`型が見つかりません: ${brief.pattern_id}`);
  const persona = brief.persona || personaDefault;
  const values = buildValues(brief, hooks);
  const exportSpec = PLATFORM_EXPORT[brief.platform] || PLATFORM_EXPORT.instagram_reels;

  const imgs = imagePrompts(pattern, persona, values);
  const vids = videoPrompts(pattern, values);
  const caps = captions(pattern, values);
  const caption = postCaption(brief, pattern, values);
  const agentPrompt = imagineAgentPrompt(brief, pattern, persona, values, vids, caps, exportSpec);

  // 検品
  const captionCheck = checkContent(caption);
  // 検品対象は「視聴者の目に触れるもの」だけ。agentPrompt は禁止語を禁止語として列挙して
  // いるため、ここに含めると必ず自己ヒットする。
  const lintTargets = [...caps.map((c) => c.text), caption];
  const lintHits = skincareLint(lintTargets, hooks.banned_in_hooks);
  const missing = collectMissing([...caps.map((c) => c.text), ...imgs.map((i) => i.prompt), agentPrompt]);

  const md = `# 動画ブリーフ: ${brief.id}

- 商品: **${brief.product}**（${brief.category}）
- 悩み: ${values.concern} / 訴求: ${values.usp || '（未設定）'}
- 型: **${pattern.name}**（\`${pattern.id}\` / ${pattern.tier}ランク）
- 尺: ${pattern.duration_sec}秒 / 必要画像: ${pattern.cuts.length}枚 / 配信先: ${brief.platform}
- link_key: \`${brief.link_key}\`

> なぜこの型か: ${pattern.why}

---

## ① ChatGPT 画像生成プロンプト

先に \`prompts/character-sheet.md\` でベース画像を1枚作り、**そのベース画像を毎回添付した上で**以下を投げる。
テキストだけで同一人物を出そうとすると必ず顔が変わる。

${imgs.map((p) => `### カット${p.n}（${p.t} ${p.role}）\n\`\`\`\n${p.prompt}\n\`\`\``).join('\n\n')}

---

## ② Grok Imagine 画像→動画プロンプト

各カットの画像をアップロードし、以下を貼る。1クリップ最大10秒（Imagine 1.0）。
被写体と動きの記述は編集しやすいよう日本語のまま残してある。指示追従が弱い時は英訳する。
動きが出ない場合は「Motion:」の動詞を強い語（drifts / unfurls / surges）に差し替える。

${vids.map((p) => `### カット${p.n}（${p.t} / ${p.sec}秒）\n\`\`\`\n${p.prompt}\n\`\`\``).join('\n\n')}

---

## ③ imagine agent 丸投げプロンプト（画像→動画 ＋ 編集）

画像 ${pattern.cuts.length} 枚と一緒に、これ1つを投げる。

\`\`\`
${agentPrompt}
\`\`\`

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
- スキンケア禁止語: ${lintHits.length === 0 ? '**なし**' : `**${lintHits.length}件** → ${lintHits.map((h) => `「${h.word}」`).join(' ')}`}
- 記入漏れ: ${missing.length === 0 ? '**なし**' : `**${missing.join(', ')}** を briefs.json の \`fill\` に追加すること`}
- 型の固有リスク: ${pattern.risk_notes}
- AIラベル: ${brief.ai_disclosure ? '**必要**（投稿時にプラットフォームのAI表示をONにする）' : '不要'}

## ⑦ Gemini 編集プロンプト

\`prompts/gemini-edit.md\` を参照。この案件の穴埋め値:
- ターゲット視聴者: ${values.concern}が気になっている20代後半〜30代前半
- プラットフォーム: ${brief.platform}
- コンテンツの傾向: ${pattern.name}
`;

  return { md, ok: captionCheck.ok && lintHits.length === 0, missing, lintHits };
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const patterns = readJSON(PATTERNS_PATH);
  const hooks = readJSON(HOOKS_PATH);
  const cfg = readJSON(BRIEFS_PATH);

  if (args.list) {
    console.log('--- 型 ---');
    for (const p of patterns.patterns) console.log(`  ${p.tier}  ${p.id.padEnd(24)} ${p.name}（${p.duration_sec}秒 / 画像${p.cuts.length}枚）`);
    console.log('--- ブリーフ ---');
    for (const b of cfg.briefs) console.log(`     ${b.id.padEnd(24)} ${b.product} / ${b.pattern_id}`);
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
    const { md, ok, missing, lintHits } = render(brief, patterns, hooks, cfg.persona);
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

module.exports = { render, fill, videoPrompts, imagePrompts, skincareLint, PLATFORM_EXPORT };
