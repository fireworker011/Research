#!/usr/bin/env node
'use strict';

/**
 * ファネル逆算計算機
 * 「月利30万」を感覚ではなく数字に分解し、シナリオ別に必要投稿力を表示する。
 *
 * 使用方法:
 *   node src/funnel-calc.js [目標金額（円）]
 */

const { loadConfig } = require('./util');

const target = parseInt(process.argv[2] || process.env.TARGET_MONTHLY_JPY || '300000', 10);

const base = loadConfig('funnel', {
  avg_commission_jpy: 5000,
  approval_rate: 0.8,
  cvr_click_to_conversion: 0.015,
  ctr_view_to_click: 0.008
});

const scenarios = [
  { name: '悲観（新規アカウント初月の典型）', commission: base.avg_commission_jpy * 0.6, approval: 0.6, cvr: 0.008, ctr: 0.004 },
  { name: '基準（config/funnel.json）', commission: base.avg_commission_jpy, approval: base.approval_rate, cvr: base.cvr_click_to_conversion, ctr: base.ctr_view_to_click },
  { name: '楽観（高単価案件比重＋型が当たった場合）', commission: base.avg_commission_jpy * 2, approval: 0.85, cvr: 0.025, ctr: 0.012 }
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
console.log('   → 悲観シナリオの数字を最初の現実として計画し、report.js の実測で毎週補正すること。\n');
