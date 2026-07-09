#!/usr/bin/env node
'use strict';

/**
 * テロップ型 Shorts 動画ジェネレータ（1080x1920・顔出しなし）
 *
 * shorts-research.js が出したネタ（タイトル/フック/台本/CTA）を、
 * そのまま投稿できるテロップ動画に変換する:
 *
 *   [フックカード 約3秒] → [台本を文単位で分割したカード群] → [CTAカード 約3秒]
 *
 * 各カードはグラデーション背景 + Noto CJK のテロップ + フェードで構成し、
 * 個別に書き出したあと連結する。BGM は YouTube Studio / CapCut 側で
 * 追加する前提（音源ライセンスの管理を制作ツールに寄せるため無音で出力）。
 *
 * 使用方法:
 *   node src/shorts-video.js                # data/shorts_proposed_ideas.json の全ネタを動画化
 *   node src/shorts-video.js --idea <ID>    # 指定ネタのみ
 *   node src/shorts-video.js --input <path> # ネタJSONを差し替え（ideas 配列を持つこと）
 *
 * video-semi-auto.js --ideas からも本モジュールの generateIdeaVideo() を使う。
 */

const fs = require('fs');
const path = require('path');
const { execFile } = require('child_process');
const { promisify } = require('util');
const { ROOT, OUTPUT_DIR, readJSON } = require('./util');

const execFileAsync = promisify(execFile);

const VIDEO_DIR = path.join(OUTPUT_DIR, 'videos');
const IDEAS_PATH = path.join(ROOT, 'data', 'shorts_proposed_ideas.json');

const WIDTH = 1080;
const HEIGHT = 1920;
const FPS = 30;
const FADE = 0.35;

// カード種別ごとの見た目（背景はダークネイビー系グラデで統一感を出す）
const STYLES = {
  hook: { fontsize: 76, color: '0xFFE066', bg: ['0x141A26', '0x25324A'] },
  body: { fontsize: 58, color: 'white', bg: ['0x141A26', '0x1F2A3D'] },
  cta: { fontsize: 58, color: '0x9EE6B8', bg: ['0x10151F', '0x1C2738'] }
};

const FONT_CANDIDATES = [
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
  '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
  '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
];

function findFont() {
  return FONT_CANDIDATES.find((f) => fs.existsSync(f)) || null;
}

/** 日本語テキストを指定文字数で折り返す（句読点の行頭禁則つき） */
function wrapText(text, charsPerLine) {
  const NO_LINE_START = '。、！？!?）」』…ー';
  const lines = [];
  for (const paragraph of String(text).split('\n')) {
    let i = 0;
    while (i < paragraph.length) {
      let end = Math.min(i + charsPerLine, paragraph.length);
      // 次行の先頭に句読点が来る場合は現在行に引き取る
      while (end < paragraph.length && NO_LINE_START.includes(paragraph[end])) end++;
      lines.push(paragraph.slice(i, end));
      i = end;
    }
  }
  return lines.join('\n');
}

/**
 * 台本を「1画面で読み切れるカード」に分割する。
 * 文単位（。！？）で切り、短い文は次とまとめて 1カード最大48文字に収める。
 */
function splitScript(script) {
  const sentences = String(script)
    .split(/(?<=[。！？!?])/)
    .map((s) => s.trim())
    .filter(Boolean);
  const cards = [];
  let buf = '';
  for (const s of sentences) {
    if (buf && (buf + s).length > 48) {
      cards.push(buf);
      buf = s;
    } else {
      buf += s;
    }
  }
  if (buf) cards.push(buf);
  return cards;
}

/** 読了時間ベースのカード表示秒数（読み切れる下限〜間延びしない上限でクランプ） */
function cardDuration(text) {
  return Math.min(6.5, Math.max(2.6, text.length * 0.14));
}

/** 1カード分の mp4 を書き出す */
async function renderCard({ text, style, duration, outPath, font }) {
  // drawtext のエスケープ地獄を避けるため、本文は textfile で渡す
  const textFile = `${outPath}.txt`;
  fs.writeFileSync(textFile, wrapText(text, style.fontsize >= 70 ? 11 : 14), 'utf-8');

  // gradients はソースフィルタのため入力（-f lavfi -i）側に置く
  const source =
    `gradients=s=${WIDTH}x${HEIGHT}:c0=${style.bg[0]}:c1=${style.bg[1]}:` +
    `x0=0:y0=0:x1=0:y1=${HEIGHT}:speed=0.01:d=${duration.toFixed(2)}`;
  const filter =
    `drawtext=fontfile='${font}':textfile='${textFile}':fontcolor=${style.color}:fontsize=${style.fontsize}:` +
    `line_spacing=26:x=(w-text_w)/2:y=(h-text_h)/2:borderw=3:bordercolor=0x0B0F16,` +
    `fade=t=in:st=0:d=${FADE},fade=t=out:st=${(duration - FADE).toFixed(2)}:d=${FADE},fps=${FPS}`;

  try {
    await execFileAsync('ffmpeg', [
      '-y',
      '-f', 'lavfi',
      '-i', source,
      '-vf', filter,
      '-c:v', 'libx264',
      '-pix_fmt', 'yuv420p',
      '-r', String(FPS),
      outPath
    ]);
  } finally {
    fs.rmSync(textFile, { force: true });
  }
}

/**
 * ネタ1本をテロップ型 Shorts 動画に変換する。
 * @param {object} idea shorts-research.js の ideas 要素（hook / script / cta を使う）
 * @param {string} outPath 出力 mp4 パス
 * @param {string} [font] フォントパス（省略時は自動検出）
 */
async function generateIdeaVideo(idea, outPath, font = findFont()) {
  if (!font) throw new Error('利用可能なフォントが見つかりません（sudo apt-get install fonts-noto-cjk）');

  const cards = [
    { text: idea.hook || idea.title, style: STYLES.hook },
    ...splitScript(idea.script).map((text) => ({ text, style: STYLES.body })),
    ...(idea.cta ? [{ text: idea.cta, style: STYLES.cta }] : [])
  ];

  const workDir = fs.mkdtempSync(path.join(require('os').tmpdir(), 'shorts-'));
  try {
    const parts = [];
    for (const [i, card] of cards.entries()) {
      const partPath = path.join(workDir, `card_${String(i).padStart(2, '0')}.mp4`);
      await renderCard({
        text: card.text,
        style: card.style,
        duration: cardDuration(card.text),
        outPath: partPath,
        font
      });
      parts.push(partPath);
    }

    // concat demuxer で連結（全カード同一パラメータなので再エンコード不要）
    const listPath = path.join(workDir, 'list.txt');
    fs.writeFileSync(listPath, parts.map((p) => `file '${p}'`).join('\n'), 'utf-8');
    fs.mkdirSync(path.dirname(outPath), { recursive: true });
    await execFileAsync('ffmpeg', ['-y', '-f', 'concat', '-safe', '0', '-i', listPath, '-c', 'copy', outPath]);
  } finally {
    fs.rmSync(workDir, { recursive: true, force: true });
  }
  return outPath;
}

async function main() {
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

  console.log(`🎬 テロップ型 Shorts 動画生成（${ideas.length}本）\n`);
  for (const idea of ideas) {
    const outPath = path.join(VIDEO_DIR, `${idea.id}.mp4`);
    process.stdout.write(`  ${idea.title} ... `);
    try {
      await generateIdeaVideo(idea, outPath);
      console.log(`✓ ${outPath}`);
    } catch (err) {
      console.log(`❌ ${err.message}`);
    }
  }
  console.log('\n✅ 完了。BGM は YouTube Studio / CapCut 側で追加してください');
}

if (require.main === module) {
  main().catch((err) => {
    console.error('\n🔴 エラー:', err.message);
    process.exit(1);
  });
}

module.exports = { generateIdeaVideo, findFont };
