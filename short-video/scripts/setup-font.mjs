#!/usr/bin/env node
// 日本語フォントを public/fonts/IPAGothic.ttf に用意する。
// フォント本体はリポジトリに入れない（6MB あるため）。環境にあるものをコピーする。
import fs from 'node:fs';
import path from 'node:path';
import { FONT_DIR, ensureDir } from './lib/paths.mjs';

const DEST = path.join(FONT_DIR, 'IPAGothic.ttf');

// 上から順に探す。IPAゴシックが第一候補（IPAフォントライセンス / 再配布可）。
const CANDIDATES = [
  '/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf',
  '/usr/share/fonts/truetype/fonts-japanese-gothic.ttf',
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',
  '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
  '/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc',
  'C:\\Windows\\Fonts\\YuGothB.ttc',
];

ensureDir(FONT_DIR);

if (fs.existsSync(DEST) && fs.statSync(DEST).size > 100_000) {
  console.log(`フォント準備済み: ${DEST}`);
  process.exit(0);
}

const found = CANDIDATES.find((p) => fs.existsSync(p));
if (!found) {
  console.error('日本語フォントが見つかりません。以下のいずれかを実行してください:');
  console.error('  Debian/Ubuntu : sudo apt-get install -y fonts-ipafont-gothic');
  console.error('  macOS         : 標準のヒラギノがあるはずです（パスを CANDIDATES に追加）');
  console.error(`  手動          : 任意の日本語 TTF を ${DEST} に置く`);
  process.exit(1);
}

fs.copyFileSync(found, DEST);
console.log(`フォントをコピーしました: ${found} → ${DEST}`);
