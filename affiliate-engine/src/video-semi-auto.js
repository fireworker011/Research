#!/usr/bin/env node
'use strict';

/**
 * YouTube Shorts / Instagram Reels 用 セミオート動画生成
 *
 * スケジュール CSV の投稿テキストを 1080x1920 の動画に変換し、
 * ユーザー確認を経て投稿キューに積む。
 *
 * 元設計からの変更点:
 * - ImageMagick の壊れたコマンド（-background に CSS gradient 構文は不可）を
 *   FFmpeg の drawtext 1本に置き換え。依存が1つ減り、日本語の折り返しも自前で処理
 * - サンプルデータ固定だったのを、実際のスケジュール CSV から本日分を読むよう変更
 * - 実アップロードは YouTube/Instagram とも OAuth 設定が必要なため、
 *   キュー（jsonl）に積むまでを自動化。アップロードは各公式ツールで行う
 *
 * 使用方法:
 *   node src/video-semi-auto.js [--date YYYY-MM-DD] [--limit N]
 */

const fs = require('fs');
const path = require('path');
const readline = require('readline');
const { execFile } = require('child_process');
const { promisify } = require('util');
const { OUTPUT_DIR, parseCSV, todayJST } = require('./util');

const execFileAsync = promisify(execFile);

const VIDEO_DIR = path.join(OUTPUT_DIR, 'videos');
const CSV_PATH = process.env.SCHEDULE_CSV || path.join(OUTPUT_DIR, 'threads_posting_schedule.csv');
const FONT_CANDIDATES = [
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
  '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
  '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc'
];

function findFont() {
  return FONT_CANDIDATES.find((f) => fs.existsSync(f)) || null;
}

/** 日本語テキストを指定文字数で折り返す */
function wrapText(text, charsPerLine = 16) {
  const lines = [];
  for (const paragraph of text.split('\n')) {
    for (let i = 0; i < paragraph.length; i += charsPerLine) {
      lines.push(paragraph.slice(i, i + charsPerLine));
    }
  }
  return lines.join('\n');
}

async function generateVideo(text, outputPath, font) {
  // drawtext 用エスケープ
  const wrapped = wrapText(text.replace(/\{\{AFFILIATE_LINK\}\}/g, 'プロフィールのリンクへ'))
    .replace(/\\/g, '\\\\')
    .replace(/'/g, "\\'")
    .replace(/:/g, '\\:')
    .replace(/%/g, '\\%');

  const filter =
    `drawtext=fontfile='${font}':text='${wrapped}':fontcolor=white:fontsize=44:` +
    `line_spacing=20:x=(w-text_w)/2:y=(h-text_h)/2`;

  await execFileAsync('ffmpeg', [
    '-y',
    '-f', 'lavfi',
    '-i', 'color=c=0x1f2430:s=1080x1920:d=7',
    '-vf', filter,
    '-c:v', 'libx264',
    '-pix_fmt', 'yuv420p',
    outputPath
  ]);
  return outputPath;
}

function ask(rl, question) {
  return new Promise((resolve) => rl.question(question, resolve));
}

function enqueue(fileName, entry) {
  const queuePath = path.join(OUTPUT_DIR, fileName);
  fs.appendFileSync(queuePath, JSON.stringify(entry) + '\n', 'utf-8');
}

async function main() {
  console.log('🎬 セミオート動画生成\n');

  const dateArg = process.argv.indexOf('--date');
  const limitArg = process.argv.indexOf('--limit');
  const targetDate = dateArg !== -1 ? process.argv[dateArg + 1] : todayJST();
  const limit = limitArg !== -1 ? parseInt(process.argv[limitArg + 1], 10) : 5;

  try {
    await execFileAsync('ffmpeg', ['-version']);
  } catch (_) {
    console.error('❌ ffmpeg がインストールされていません（sudo apt-get install ffmpeg）');
    process.exit(1);
  }
  const font = findFont();
  if (!font) {
    console.error('❌ 利用可能なフォントが見つかりません（sudo apt-get install fonts-noto-cjk）');
    process.exit(1);
  }

  if (!fs.existsSync(CSV_PATH)) {
    console.error(`❌ スケジュール CSV がありません: ${CSV_PATH}`);
    process.exit(1);
  }
  const schedule = parseCSV(fs.readFileSync(CSV_PATH, 'utf-8'));
  const posts = schedule.filter((r) => r.date === targetDate).slice(0, limit);

  if (posts.length === 0) {
    console.log(`${targetDate} の投稿はスケジュールにありません`);
    return;
  }

  fs.mkdirSync(VIDEO_DIR, { recursive: true });
  const rl = readline.createInterface({ input: process.stdin, output: process.stdout });

  for (const post of posts) {
    console.log(`\n${'='.repeat(50)}`);
    console.log(`📅 ${post.date} ${post.time} | ${post.genre} | @${post.account}`);
    console.log(`${'='.repeat(50)}`);
    console.log(post.content);

    const fileName = `${post.date}_${post.time.replace(':', '-')}_${post.account}.mp4`;
    const videoPath = path.join(VIDEO_DIR, fileName);

    console.log('\n🎬 動画生成中...');
    try {
      await generateVideo(`${post.content}\n${post.emoji || ''}`, videoPath, font);
      console.log(`  ✓ ${videoPath}`);
    } catch (err) {
      console.error(`  ❌ 生成失敗: ${err.message}`);
      continue;
    }

    const answer = await ask(rl, '\n[y]キューに追加 / [e]編集して追加 / [s]スキップ / [q]終了 : ');
    if (answer === 'q') break;
    if (answer === 's') continue;

    let content = post.content;
    if (answer === 'e') {
      content = (await ask(rl, '新しい本文: ')) || content;
      await generateVideo(`${content}\n${post.emoji || ''}`, videoPath, font);
    }
    if (answer === 'y' || answer === 'e') {
      const meta = {
        timestamp: new Date().toISOString(),
        videoPath,
        genre: post.genre,
        title: `【${post.genre}】${content.split('\n')[0].slice(0, 40)}`,
        description: `${content}\n#PR`,
        status: 'queued'
      };
      enqueue('youtube_uploads.jsonl', meta);
      enqueue('instagram_uploads.jsonl', { ...meta, caption: `${content}\n\n#${post.genre} #PR` });
      console.log('  ✓ YouTube / Instagram キューに追加');
    }
  }

  rl.close();
  console.log(`\n✅ 完了。キュー: ${path.join(OUTPUT_DIR, 'youtube_uploads.jsonl')}`);
  console.log('   アップロードは YouTube Studio / Meta Business Suite の予約投稿で行ってください');
}

main().catch((err) => {
  console.error('\n🔴 エラー:', err.message);
  process.exit(1);
});
