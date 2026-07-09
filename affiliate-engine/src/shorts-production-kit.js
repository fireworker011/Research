#!/usr/bin/env node
'use strict';

/**
 * Grok + CapCut 制作キット生成
 *
 * 採用した Shorts ネタ（shorts-research.js の出力）を、以下の手作業フローに
 * そのまま渡せる形式にパッケージングする:
 *
 *   Grok で画像を複数枚生成 → Grok で画像から動画化（アニメーション化）
 *   → Grok Companion にナレーションを読み上げさせる → CapCut で編集して投稿
 *
 * このスクリプトは動画そのものは生成しない（動画化は Grok / 編集は CapCut が担当）。
 * 出す成果物は「コピペで作業を始められるプロンプト集」までで、これが半自動の境界線。
 *
 * 使用方法:
 *   node src/shorts-production-kit.js                # 採用待ちネタ全件をパッケージング
 *   node src/shorts-production-kit.js --idea <ID>     # 指定ネタのみ
 *   node src/shorts-production-kit.js --input <path>  # ネタJSONを差し替え
 */

const fs = require('fs');
const path = require('path');
const { ROOT, OUTPUT_DIR, readJSON, todayJST } = require('./util');

const IDEAS_PATH = path.join(ROOT, 'data', 'shorts_proposed_ideas.json');
const PRODUCTION_DIR = path.join(OUTPUT_DIR, 'shorts', 'production');

/** ネタ1本の制作キット（Markdown）を組み立てる */
function renderKit(idea) {
  const lines = [`# ${idea.title}`, ''];
  lines.push(`チャンネル: ${idea.genre} (${idea.channel}) ／ 予測: ${idea.engagement_prediction || '-'}`);
  lines.push('');
  lines.push('## 手順');
  lines.push('');
  lines.push('1. 下記「Grok 画像プロンプト」を1枚ずつ Grok の画像生成に貼り、9:16 の画像を人数分生成する');
  lines.push('2. 各画像を Grok の動画化機能に渡し、「動画化」欄のアニメーション指示を添えて短尺クリップにする');
  lines.push('3. 「ナレーション台本」を `narration.txt` からコピーして Grok Companion に読み上げさせ、音声を書き出す');
  lines.push('4. CapCut に動画クリップ（生成順）+ ナレーション音声を読み込み、下記チェックリストの順に編集する');
  lines.push('5. 概要欄に「概要欄・投稿メタ」の内容を貼って投稿（YouTube Studio 予約投稿）');
  lines.push('');
  lines.push('## フック（冒頭2秒・字幕/最初のセリフに使う）');
  lines.push('');
  lines.push(idea.hook || '-');
  lines.push('');
  lines.push('## Grok 画像プロンプト');
  lines.push('');
  for (const p of idea.image_prompts || []) {
    lines.push(`### ${p.order}枚目`);
    lines.push('');
    lines.push('```');
    lines.push(p.prompt);
    lines.push('```');
    if (p.motion) lines.push(`**動画化（アニメーション指示）**: ${p.motion}`);
    lines.push('');
  }
  if ((idea.image_prompts || []).length === 0) {
    lines.push('_画像プロンプトが生成されていません（旧フォーマットのネタ、またはネタ出しに失敗した可能性）。再生成を推奨_');
    lines.push('');
  }
  lines.push('## CapCut 編集チェックリスト');
  lines.push('');
  lines.push('- [ ] 画像→動画クリップを生成順に並べる（フック用の1枚目を最初に）');
  lines.push('- [ ] ナレーション音声を全体にオーバーレイし、クリップの切り替えを台詞の区切りに合わせる');
  lines.push('- [ ] フック部分に画面テキストとしてフックの文言を大きく表示（最初の2秒で離脱させない）');
  lines.push('- [ ] BGM を追加（音量はナレーションの邪魔にならない程度に下げる）');
  lines.push('- [ ] 自動字幕 or 手動キャプションを全編に付ける（無音視聴対応）');
  lines.push(`- [ ] 締めに「${idea.cta || ''}」のテロップ/ナレーションを入れる`);
  lines.push('- [ ] 縦動画 1080x1920・尺 60秒以内で書き出し');
  lines.push('');
  lines.push('## 概要欄・投稿メタ');
  lines.push('');
  lines.push(`**タイトル**: ${idea.title}`);
  lines.push('');
  lines.push(`**ハッシュタグ**: ${(idea.hashtags || []).join(' ')}`);
  lines.push('');
  if (idea.link_key) {
    lines.push(`**アフィリエイトリンク**: config/links.json の \`${idea.link_key}\` を概要欄先頭に貼り、末尾に \`#PR\` を付ける（景表法対応・必須）`);
  } else {
    lines.push('**アフィリエイトリンクなし**（価値提供ネタ。登録・保存を促すのみ）');
  }
  lines.push('');
  return lines.join('\n');
}

function buildKit(idea, baseDir = PRODUCTION_DIR) {
  const dir = path.join(baseDir, idea.id);
  fs.mkdirSync(dir, { recursive: true });
  const kitPath = path.join(dir, 'kit.md');
  const narrationPath = path.join(dir, 'narration.txt');
  fs.writeFileSync(kitPath, renderKit(idea), 'utf-8');
  fs.writeFileSync(narrationPath, idea.script || '', 'utf-8');
  return { dir, kitPath, narrationPath };
}

function main() {
  const inputArg = process.argv.indexOf('--input');
  const ideaArg = process.argv.indexOf('--idea');
  const inputPath = inputArg !== -1 ? process.argv[inputArg + 1] : IDEAS_PATH;

  const proposed = readJSON(inputPath, null);
  if (!proposed || (proposed.ideas || []).length === 0) {
    console.error(`❌ ネタがありません: ${inputPath}（先に node src/shorts-research.js を実行）`);
    process.exit(1);
  }
  let ideas = proposed.ideas;
  if (ideaArg !== -1) {
    const id = process.argv[ideaArg + 1];
    ideas = ideas.filter((i) => i.id === id);
    if (ideas.length === 0) {
      console.error(`❌ 指定IDのネタが見つかりません: ${id}`);
      console.error(`   利用可能: ${proposed.ideas.map((i) => i.id).join(', ')}`);
      process.exit(1);
    }
  }

  console.log(`🎬 Grok + CapCut 制作キット生成（${ideas.length}本）\n`);
  for (const idea of ideas) {
    const { dir } = buildKit(idea);
    console.log(`  ✓ ${idea.title}\n    → ${dir}`);
  }
  console.log(`\n✅ 完了。各フォルダの kit.md の手順どおりに Grok → CapCut で制作してください`);
}

if (require.main === module) {
  main();
}

module.exports = { buildKit, renderKit };
