#!/usr/bin/env node
'use strict';

/**
 * ファネル逆算計算機
 * 「月利30万」を感覚ではなく数字に分解し、シナリオ別に必要投稿力を表示する。
 *
 * 使用方法:
 *   node src/funnel-calc.js [目標金額（円）]
 *   node src/funnel-calc.js [目標金額（円）] --genre 婚活   # そのジャンルの単価で試算
 *   node src/funnel-calc.js --rank                          # ジャンル別単価ランキングのみ表示
 */

const { loadConfig } = require('./util');

function parseArgs(argv) {
  const args = { target: null, genre: null, rank: false };
  for (let i = 0; i < argv.length; i++) {
    if (argv[i] === '--genre') args.genre = argv[++i];
    else if (argv[i] === '--rank') args.rank = true;
    else if (!isNaN(parseInt(argv[i], 10))) args.target = parseInt(argv[i], 10);
  }
  return args;
}

const args = parseArgs(process.argv.slice(2));
const target = args.target || parseInt(process.env.TARGET_MONTHLY_JPY || '300000', 10);

const base = loadConfig('funnel', {
  avg_commission_jpy: 5000,
  approval_rate: 0.8,
  cvr_click_to_conversion: 0.015,
  ctr_view_to_click: 0.008,
  commission_by_genre: {}
});

const byGenre = base.commission_by_genre || {};
const ranked = Object.entries(byGenre).sort((a, b) => b[1].jpy - a[1].jpy);

function printRanking() {
  console.log('\n💰 ジャンル別 想定単価ランキング（高い順）\n');
  for (const [genre, v] of ranked) {
    const mark = v.confidence === 'sourced' ? '' : '（未確認）';
    console.log(`   ${String(v.jpy).padStart(6)}円  ${genre.padEnd(6)} ${v.note}${mark}`);
  }
  console.log('\n※ estimate は未確認の推定値。実額は各ASPプログラム詳細で必ず確認すること。\n');
}

if (args.rank) {
  printRanking();
  process.exit(0);
}

let commissionBase = base.avg_commission_jpy;
let label = 'config/funnel.json の一律想定';
if (args.genre) {
  const hit = byGenre[args.genre];
  if (!hit) {
    console.error(`🔴 ジャンル「${args.genre}」が commission_by_genre に見つかりません。--rank で一覧を確認してください`);
    process.exit(1);
  }
  commissionBase = hit.jpy;
  label = `${args.genre}（${hit.link_key}）想定単価${hit.confidence === 'sourced' ? '' : '・未確認'}`;
}

const scenarios = [
  { name: '悲観（新規アカウント初月の典型）', commission: commissionBase * 0.6, approval: 0.6, cvr: 0.008, ctr: 0.004 },
  { name: `基準（${label}）`, commission: commissionBase, approval: base.approval_rate, cvr: base.cvr_click_to_conversion, ctr: base.ctr_view_to_click },
  { name: '楽観（高単価案件比重＋型が当たった場合）', commission: commissionBase * 2, approval: 0.85, cvr: 0.025, ctr: 0.012 }
];

console.log(`\n🎯 目標: ¥${target.toLocaleString()}/月（確定ベース）\n`);

for (const s of scenarios) {
  const conversions = Math.ceil(target / s.approval / s.commission);
  const clicks = Math.ceil(conversions / s.cvr);
  const views = Math.ceil(clicks / s.ctr);
  const viewsPerDay = Math.ceil(views / 30);
  // 3投稿/日 × アカウント数で割った必要平均views/投稿
  const perPost = (n) => Math.ceil(viewsPerDay / (3 * n)).toLocaleString();

  console.log(`━━ ${s.name}`);
  console.log(`   単価 ¥${Math.round(s.commission).toLocaleString()} / 承認率 ${Math.round(s.approval * 100)}% / CVR ${s.cvr * 100}% / CTR ${s.ctr * 100}%`);
  console.log(`   必要成約: ${conversions} 件/月`);
  console.log(`   必要クリック: ${clicks.toLocaleString()} 回/月`);
  console.log(`   必要ビュー: ${views.toLocaleString()} 回/月 = ${viewsPerDay.toLocaleString()} 回/日`);
  console.log(`   必要平均views/投稿: 3アカ運用 ${perPost(3)} / 5アカ運用 ${perPost(5)}`);
  console.log('');
}

console.log('※ 新規アカウントの平均views/投稿は最初 数十〜数百。数千に届くのは型が当たった場合。');
console.log('   → 悲観シナリオの数字を最初の現実として計画し、report.js の実測で毎週補正すること。');
if (!args.genre && ranked.length) {
  console.log(`   → --genre <ジャンル名> で単価を差し替えて試算できる。--rank でジャンル別ランキングを見る。\n`);
} else {
  console.log('');
}
