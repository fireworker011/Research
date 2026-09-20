#!/usr/bin/env node
'use strict';

/**
 * FANZA/DMMアダのファネル逆算。
 * 公式で確認できた上限と、未確認の仮定を混ぜない。
 *
 *   node src/adult-funnel.js [目標金額]
 *   node src/adult-funnel.js --self-test
 */

const { loadConfig } = require('./util');

const DEFAULT_ASSUMPTIONS = {
  avg_commission_jpy: 1050,
  approval_rate: 0.8,
  cvr_click_to_conversion: 0.01,
  ctr_impression_to_click: 0.01
};

function loadAdultFunnel() {
  const raw = loadConfig('adult-funnel', {});
  const official = raw.official || {};
  const assumptions = { ...DEFAULT_ASSUMPTIONS, ...(raw.assumptions || {}) };
  return { official, assumptions };
}

function requiredFor(target, s) {
  const conversions = Math.ceil(target / s.approval / s.commission);
  const clicks = Math.ceil(conversions / s.cvr);
  const impressions = Math.ceil(clicks / s.ctr);
  return {
    conversions,
    clicks,
    impressions,
    impressionsPerDay: Math.ceil(impressions / 30)
  };
}

function scenariosFrom(assumptions) {
  return [
    {
      name: '悲観（仮定。公式値ではない）',
      commission: assumptions.avg_commission_jpy * 0.5,
      approval: 0.6,
      cvr: 0.005,
      ctr: 0.005
    },
    {
      name: '基準（config/adult-funnel.json の仮定）',
      commission: assumptions.avg_commission_jpy,
      approval: assumptions.approval_rate,
      cvr: assumptions.cvr_click_to_conversion,
      ctr: assumptions.ctr_impression_to_click
    },
    {
      name: '楽観（仮定。公式の最大料率を実績と読むな）',
      commission: assumptions.avg_commission_jpy * 2,
      approval: 0.85,
      cvr: 0.02,
      ctr: 0.02
    }
  ];
}

function render(target, official, assumptions) {
  const lines = [];
  lines.push(`目標: ¥${target.toLocaleString()}/月（確定ベース）`);
  lines.push('');
  lines.push('公式で確認できたこと（affiliate.dmm.com / support.dmm.co.jp、2026-08-22取得）:');
  lines.push(
    `- ダイレクト報酬 最大${official.direct_reward_max_pct ?? 70}% / サービス新規 最大¥${(official.new_user_reward_max_jpy ?? 5240).toLocaleString()} / カテゴリ報酬 最大${official.category_reward_max_pct ?? 20}%`
  );
  lines.push(
    `- 支払: 月末締め翌月10日。下限 ¥${(official.payout_min_jpy ?? 5000).toLocaleString()}（[支払いヘルプ](https://support.dmm.co.jp/affiliate/article/44530)）`
  );
  lines.push('- 先月ランキング上位はアフィリエイター単位で数百万円。新規の中央値ではない');
  lines.push('- カテゴリ別の「今の」料率はログイン後の報酬料率ページでしか確定できない');
  lines.push('');
  lines.push('仮定（公式ではない。管理画面の実測で上書きすること）:');
  lines.push(
    `- 平均報酬 ¥${assumptions.avg_commission_jpy} / 承認率 ${assumptions.approval_rate} / CVR ${assumptions.cvr_click_to_conversion} / CTR ${assumptions.ctr_impression_to_click}`
  );
  lines.push('');

  const firstCash = official.payout_min_jpy || 5000;
  lines.push(`最初に語る目標は月100万ではない。最初の現金ゲートは ¥${firstCash.toLocaleString()}。`);
  lines.push('');

  for (const label of [
    { title: `現金ゲート ¥${firstCash.toLocaleString()}`, amount: firstCash },
    { title: `目標 ¥${target.toLocaleString()}`, amount: target }
  ]) {
    lines.push(`== ${label.title}`);
    for (const s of scenariosFrom(assumptions)) {
      const n = requiredFor(label.amount, s);
      lines.push(`-- ${s.name}`);
      lines.push(
        `   単価 ¥${Math.round(s.commission).toLocaleString()} / 承認率 ${Math.round(s.approval * 100)}% / CVR ${s.cvr * 100}% / CTR ${s.ctr * 100}%`
      );
      lines.push(`   必要成約: ${n.conversions} 件`);
      lines.push(`   必要クリック: ${n.clicks.toLocaleString()} 回`);
      lines.push(
        `   必要表示: ${n.impressions.toLocaleString()} 回（${n.impressionsPerDay.toLocaleString()} 回/日）`
      );
    }
    lines.push('');
  }

  lines.push('YouTube / TikTok / Instagram の表示数をここに入れない。');
  lines.push('あの3媒体は性的コンテンツと成人サイト誘導を禁止している。数字が良く見えても使えない。');
  lines.push('');
  return `${lines.join('\n')}\n`;
}

function assertEqual(actual, expected, label) {
  if (actual !== expected) {
    throw new Error(`${label}: expected ${expected}, got ${actual}`);
  }
}

function runSelfTest() {
  const n = requiredFor(1000000, {
    commission: 1050,
    approval: 0.8,
    cvr: 0.01,
    ctr: 0.01
  });
  assertEqual(n.conversions, Math.ceil(1000000 / 0.8 / 1050), 'conversions');
  assertEqual(n.clicks, Math.ceil(n.conversions / 0.01), 'clicks');
  assertEqual(n.impressions, Math.ceil(n.clicks / 0.01), 'impressions');

  const cash = requiredFor(5000, {
    commission: 1050,
    approval: 0.8,
    cvr: 0.01,
    ctr: 0.01
  });
  if (cash.clicks >= n.clicks) throw new Error('first cash must need fewer clicks than 1M');

  const text = render(1000000, { payout_min_jpy: 5000 }, DEFAULT_ASSUMPTIONS);
  if (!text.includes('仮定')) throw new Error('must label assumptions');
  if (!text.includes('YouTube')) throw new Error('must warn platforms');
  console.log('self-test ok');
}

function main() {
  if (process.argv.includes('--self-test')) {
    runSelfTest();
    return;
  }
  const target = parseInt(process.argv[2] || process.env.TARGET_MONTHLY_JPY || '1000000', 10);
  const { official, assumptions } = loadAdultFunnel();
  process.stdout.write(render(target, official, assumptions));
}

module.exports = { requiredFor, scenariosFrom, render, loadAdultFunnel, DEFAULT_ASSUMPTIONS };

if (require.main === module) {
  try {
    main();
  } catch (err) {
    console.error(`adult-funnel failed: ${err.message}`);
    process.exit(1);
  }
}
