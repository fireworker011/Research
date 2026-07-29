#!/usr/bin/env node
// STEP2: script.json の検証。
//   構造（シーン数 / 先頭フック / 末尾CTA / telop_style）と
//   表現（収益の断定・誇大表現・景表法まわり）を機械的に検品する。
// 落ちる = 投稿前に人が直すべきもの。warn = 出力はできるが確認推奨。
import { loadScript } from './lib/paths.mjs';

const TELOP_STYLES = new Set(['title', 'paren', 'normal']);
const TELOP_MAX = 14; // 縦1080pxで1行に収まる上限の目安
const ROLES = new Set(['title', 'body', 'cta']);

// 断定的な収益表現・誇大表現。景品表示法（優良誤認・有利誤認）対策。
const BANNED = [
  { re: /必ず(儲|稼|勝|成功)/, why: '収益・成果の断定' },
  { re: /(絶対|確実)に?(儲|稼|勝|成功|痩)/, why: '成果の断定' },
  { re: /誰でも(必ず|絶対|簡単に)?\s*(月|日給|年収)?\s*\d/, why: '再現性の断定' },
  { re: /月収?\s*\d+\s*万\s*(円)?(稼|保証|確定|達成できる)/, why: '具体的収益の保証' },
  { re: /(不労所得|自動的に)(で|が)?(稼|入っ|増え)/, why: '不労所得の断定' },
  { re: /元本保証|損しない|ノーリスク|リスクゼロ/, why: 'リスクの否定' },
  { re: /日本一|世界一|No\.?1|業界最安/, why: '最上級表現（根拠の明示が必要）' },
  { re: /(完全|100%)無料(で稼|で儲)/, why: '無料訴求と収益の結合' },
];

// TTS に渡す前に直したい表記ゆれ・誤字（script.json 自体は確定稿なので触らない）
const SUSPECT_CHARS = /[时东关发这个说话觉验对]/;

const script = loadScript();
const errors = [];
const warnings = [];

const fail = (m) => errors.push(m);
const warn = (m) => warnings.push(m);

// --- 全体構造 ---
if (!script.title) fail('title がありません');
if (!script.caption) fail('caption がありません');
if (!Array.isArray(script.sentences) || script.sentences.length === 0) {
  fail('sentences が空です');
  report();
}

const s = script.sentences;

if (s.length < 8) warn(`シーン数が ${s.length} 件。ショートは 8〜16 件が目安です`);
if (s.length > 20) warn(`シーン数が ${s.length} 件。長すぎて離脱しやすい可能性があります`);

// --- フック（先頭） ---
if (s[0].role !== 'title') fail('先頭シーンの role が title ではありません（フック不足）');

// --- CTA（末尾2） ---
const tail = s.slice(-2);
if (!tail.every((x) => x.role === 'cta')) {
  fail('末尾2シーンが cta ではありません');
}
const ctaText = tail.map((x) => x.narration).join('');
if (!ctaText.includes('やり方はXで')) {
  warn('末尾CTAに指定文言「やり方はXで」が含まれていません');
}

// --- 各シーン ---
s.forEach((sc, i) => {
  const tag = `sentences[${i}]`;
  if (!ROLES.has(sc.role)) fail(`${tag}: role が不正 (${sc.role})`);
  if (!sc.narration?.trim()) fail(`${tag}: narration が空です`);
  if (!sc.telop?.trim()) fail(`${tag}: telop が空です`);
  if (!TELOP_STYLES.has(sc.telop_style)) fail(`${tag}: telop_style が不正 (${sc.telop_style})`);

  if (sc.telop && [...sc.telop].length > TELOP_MAX) {
    warn(`${tag}: telop が ${[...sc.telop].length} 文字。${TELOP_MAX} 文字以内推奨「${sc.telop}」`);
  }
  if (sc.narration && [...sc.narration].length > 60) {
    warn(`${tag}: narration が長め（${[...sc.narration].length} 文字）。約5秒を超える可能性があります`);
  }
  if (sc.narration && SUSPECT_CHARS.test(sc.narration)) {
    warn(`${tag}: 日本語では使わない字が含まれています（TTS で誤読の恐れ）「${sc.narration}」`);
  }
});

// --- 表現チェック（台本 + キャプション） ---
const allText = [script.title, script.caption, ...s.flatMap((x) => [x.narration, x.telop])].join('\n');
for (const { re, why } of BANNED) {
  const hit = allText.match(re);
  if (hit) fail(`表現NG: ${why} → 「${hit[0]}」`);
}

// --- キャプション ---
if ([...script.caption].length > 140) {
  warn(`caption が ${[...script.caption].length} 文字。プラットフォームにより途中で省略されます`);
}
if (!/#/.test(script.caption)) warn('caption にハッシュタグがありません');

report();

function report() {
  const total = s?.length ?? 0;
  console.log('=== STEP2 台本検証 ===');
  console.log(`シーン数     : ${total}`);
  console.log(`先頭フック   : ${s?.[0]?.telop ?? '-'} (${s?.[0]?.role ?? '-'})`);
  console.log(`末尾CTA      : ${s?.slice(-2).map((x) => x.role).join(', ') ?? '-'}`);
  console.log(`推定尺       : 約 ${estimateTotalSeconds(s).toFixed(1)} 秒`);
  console.log('');

  for (const w of warnings) console.log(`  [warn]  ${w}`);
  for (const e of errors) console.log(`  [ERROR] ${e}`);

  if (errors.length) {
    console.log(`\nNG: ${errors.length} 件のエラー。修正してから STEP3 へ進んでください。`);
    process.exit(1);
  }
  console.log(`\nOK: 検証通過${warnings.length ? `（warn ${warnings.length} 件）` : ''}。STEP3 へ進めます。`);
}

function estimateTotalSeconds(sentences = []) {
  return sentences.reduce((acc, sc) => acc + [...(sc.narration ?? '')].length / 7.2 + 0.35, 0);
}
