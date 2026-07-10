#!/usr/bin/env node
'use strict';

/**
 * Grok Agent Mode + CapCut 制作キット生成
 *
 * 採用した Shorts ネタ（shorts-research.js の出力）を、以下の手作業フローに
 * そのまま渡せる形式にパッケージングする:
 *
 *   Grok Agent Mode に1本のプロンプトを投げて画像生成〜動画化まで一括実行
 *   → Grok Companion にナレーションを読み上げさせて音声を抽出
 *   → CapCut で映像+音声+BGM+字幕を編集して投稿
 *
 * 出力（output/shorts/production/<ネタID>/）:
 *   kit.md               手順・CapCutチェックリスト・概要欄メタ（リンクURL入り）
 *   grok_agent_prompt.txt Grok Agent Mode にそのまま貼る一括生成プロンプト
 *   narration.txt         Grok Companion に読ませるナレーション台本
 *
 * このスクリプトは動画そのものは生成しない（生成は Grok / 編集は CapCut が担当）。
 * 「コピペで作業を始められる状態」までが自動化の境界線。
 *
 * 案件差し替えについて: 台本・CTA は商品名を含まない設計（shorts-research.js 側で強制）。
 * 案件を変えるときは config/links.json の該当キーの URL を差し替えるだけでよく、
 * 過去動画も概要欄のリンクを貼り替えれば資産として生き続ける。
 *
 * 使用方法:
 *   node src/shorts-production-kit.js                # 採用待ちネタ全件をパッケージング
 *   node src/shorts-production-kit.js --idea <ID>     # 指定ネタのみ
 *   node src/shorts-production-kit.js --input <path>  # ネタJSONを差し替え
 */

const fs = require('fs');
const path = require('path');
const { ROOT, OUTPUT_DIR, readJSON, loadConfig } = require('./util');

const IDEAS_PATH = path.join(ROOT, 'data', 'shorts_proposed_ideas.json');
const PRODUCTION_DIR = path.join(OUTPUT_DIR, 'shorts', 'production');

/** Grok Agent Mode に貼る一括生成プロンプトを組み立てる */
function renderAgentPrompt(idea) {
  const prompts = idea.image_prompts || [];
  const lines = [];
  lines.push('あなたに YouTube Shorts 用の素材生成を一括で依頼します。以下を順番にすべて実行してください。');
  lines.push('');
  lines.push(`【全体の条件】`);
  lines.push('- すべて縦 9:16（1080x1920 相当）で生成する');
  lines.push('- 全カットでスタイル・色調・世界観を統一する（同じ動画のカットとして違和感がないこと）');
  lines.push('- 文字入れはしない（テロップは後工程の CapCut で入れるため、画像・動画に文字を焼き込まない）');
  lines.push(`- カットは全部で${prompts.length}枚。まず${prompts.length}枚の画像を生成し、次に各画像を指定のアニメーション指示で約5秒の動画クリップにする`);
  lines.push('');
  for (const p of prompts) {
    lines.push(`【カット${p.order}】`);
    lines.push(`画像: ${p.prompt}`);
    if (p.motion) lines.push(`動画化: ${p.motion}`);
    lines.push('');
  }
  lines.push('すべてのクリップを生成し終えたら、カット番号順に並べてダウンロードできる状態にしてください。');
  return lines.join('\n');
}

/** ネタ1本の制作キット（Markdown）を組み立てる */
function renderKit(idea) {
  const links = loadConfig('links', {});
  const linkUrl = idea.link_key ? links[idea.link_key] || '' : '';

  const lines = [`# ${idea.title}`, ''];
  lines.push(`チャンネル: ${idea.genre} (${idea.channel}) ／ 予測: ${idea.engagement_prediction || '-'}`);
  lines.push('');
  lines.push('## 手順');
  lines.push('');
  lines.push('1. `grok_agent_prompt.txt` の中身を丸ごと Grok Agent Mode に貼る → 画像生成〜動画クリップ化まで一括で実行される');
  lines.push('2. `narration.txt` を Grok Companion に読み上げさせ、音声を抽出する');
  lines.push('3. CapCut にクリップ（カット番号順）+ ナレーション音声を読み込み、下記チェックリストの順に編集する');
  lines.push('4. 「概要欄・投稿メタ」をコピペして YouTube Studio で予約投稿する');
  lines.push('');
  lines.push('## フック（冒頭2秒・CapCut で最初に入れるテロップ）');
  lines.push('');
  lines.push(idea.hook || '-');
  lines.push('');
  if ((idea.image_prompts || []).length === 0) {
    lines.push('## ⚠️ 画像プロンプトなし');
    lines.push('');
    lines.push('_このネタには画像プロンプトが生成されていません（旧フォーマット、または生成失敗）。shorts-research.js の再実行を推奨_');
    lines.push('');
  }
  lines.push('## CapCut 編集チェックリスト');
  lines.push('');
  lines.push('- [ ] クリップをカット番号順に並べる（1カット目=フックに対応）');
  lines.push('- [ ] ナレーション音声を全体にオーバーレイし、カットの切り替えを台詞の区切りに合わせる');
  lines.push('- [ ] 冒頭にフックのテロップを大きく表示（最初の2秒で離脱させない）');
  lines.push('- [ ] 自動字幕 or 手動キャプションを全編に付ける（無音視聴対応）');
  lines.push('- [ ] BGM を追加（音量はナレーションの邪魔にならない程度に下げる）');
  lines.push(`- [ ] 締めに「${idea.cta || ''}」のテロップ/ナレーションを確認`);
  lines.push('- [ ] 縦動画 1080x1920・尺 60秒以内で書き出し');
  lines.push('');
  lines.push('## 概要欄・投稿メタ');
  lines.push('');
  lines.push(`**タイトル**: ${idea.title}`);
  lines.push('');
  lines.push(`**ハッシュタグ**: ${(idea.hashtags || []).join(' ')}`);
  lines.push('');
  if (idea.link_key) {
    if (linkUrl) {
      lines.push(`**概要欄に貼るリンク**（${idea.link_key}）: ${linkUrl}`);
      lines.push('');
      lines.push('- 概要欄の先頭にリンク、末尾に `#PR` を必ず入れる（景表法のステマ規制対応）');
      lines.push('- 投稿前にリンクを一度開いて生きているか確認する（案件終了・在庫切れで無効になっていることがある）');
    } else {
      lines.push(`**⚠️ リンク未設定**: config/links.json の \`${idea.link_key}\` に URL を入れてから投稿すること（#PR も忘れずに）`);
    }
  } else {
    lines.push('**アフィリエイトリンクなし**（価値提供ネタ。登録・保存を促すのみ）');
  }
  lines.push('');
  lines.push('---');
  lines.push('案件を差し替えたくなったら: config/links.json の該当キーの URL を変えるだけ。動画・台本は商品名を含まないので作り直し不要（過去動画は概要欄のリンクを貼り替える）');
  lines.push('');
  return lines.join('\n');
}

function buildKit(idea, baseDir = PRODUCTION_DIR) {
  const dir = path.join(baseDir, idea.id);
  fs.mkdirSync(dir, { recursive: true });
  fs.writeFileSync(path.join(dir, 'kit.md'), renderKit(idea), 'utf-8');
  fs.writeFileSync(path.join(dir, 'grok_agent_prompt.txt'), renderAgentPrompt(idea), 'utf-8');
  fs.writeFileSync(path.join(dir, 'narration.txt'), idea.script || '', 'utf-8');
  return dir;
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

  console.log(`🎬 Grok Agent Mode + CapCut 制作キット生成（${ideas.length}本）\n`);
  for (const idea of ideas) {
    const dir = buildKit(idea);
    console.log(`  ✓ ${idea.title}\n    → ${dir}`);
  }
  console.log('\n✅ 完了。各フォルダの kit.md の手順どおりに制作してください');
  console.log('   （grok_agent_prompt.txt → Grok Agent Mode / narration.txt → Grok Companion / 仕上げ CapCut）');
}

if (require.main === module) {
  main();
}

module.exports = { buildKit, renderKit, renderAgentPrompt };
