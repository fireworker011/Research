'use strict';
// 現在の市況を取得し、「次の5分足が上がる確率」を過去データの頻度から算出する。
// 使い方: node src/predict.js USDJPY [--payout=1.88]
//
// 出力される確率は「過去60日で現在と同じ条件だった場面のうち、実際に次足が
// 陽線になった割合」であり、モデルによる推論・予想は含まない。

const { fetchCandles, saveCache } = require('./fetch');
const { buildTables, extractConditions, buildContext, wilson, poolEstimates } = require('./stats');

function fmtPct(x) {
  return (x * 100).toFixed(1) + '%';
}

function fmtPrice(x) {
  // JPYクロスは小数3桁、それ以外(EURUSD等)は5桁が慣例
  return x >= 20 ? x.toFixed(3) : x.toFixed(5);
}

function jstString(unixSec) {
  return new Date((unixSec + 9 * 3600) * 1000).toISOString().replace('T', ' ').slice(0, 16) + ' JST';
}

async function main() {
  const args = process.argv.slice(2);
  const pair = (args.find((a) => !a.startsWith('--')) || 'USDJPY').toUpperCase();
  const payoutArg = args.find((a) => a.startsWith('--payout='));
  const payout = payoutArg ? parseFloat(payoutArg.split('=')[1]) : 1.88;

  console.log(`${pair} の最新データを取得中...`);
  const data = await fetchCandles(pair);
  saveCache(data);
  const candles = data.candles;
  const now = Math.floor(Date.now() / 1000);

  // 最後の足が形成中(開始から5分未満)なら、その1本前を「直近の確定足」とする
  let lastIdx = candles.length - 1;
  const forming = now < candles[lastIdx].t + 300;
  if (forming) lastIdx -= 1;
  const lastCandle = candles[lastIdx];

  // 市場クローズ判定: 確定足が15分以上前なら配信が止まっている(週末など)
  if (now - lastCandle.t > 15 * 60) {
    console.log(`\n⚠ 直近の確定足が ${jstString(lastCandle.t)} と古く、市場が閉まっているか配信停止中です。`);
    console.log('この状態での予測は意味を持たないため中止します。');
    process.exit(2);
  }

  const { tables } = buildTables(candles);
  const ctx = buildContext(candles);
  const conds = extractConditions(candles, lastIdx, ctx);
  const targetOpen = lastCandle.t + 300;

  console.log(`\n=== ${pair} 次足予測 ===`);
  console.log(`直近確定足: ${jstString(lastCandle.t)} 始値${fmtPrice(lastCandle.o)} → 終値${fmtPrice(lastCandle.c)} (${lastCandle.c > lastCandle.o ? '陽線' : lastCandle.c < lastCandle.o ? '陰線' : '同値'})`);
  console.log(`予測対象足: ${jstString(targetOpen)} 開始の5分足`);
  console.log(`現在価格: ${fmtPrice(data.marketPrice)}`);

  console.log('\n--- 現在の条件と、過去60日の同条件での実績 ---');
  const estimates = [];
  for (const [factor, value] of Object.entries(conds)) {
    const s = tables[factor] && tables[factor][value];
    if (!s || s.n === 0) {
      console.log(`${factor}: ${value} → 過去データに同条件なし`);
      continue;
    }
    const w = wilson(s.up, s.n);
    estimates.push({ factor, value, ...s, ...w });
    const sig = w.lo > 0.5 ? '↑有意' : w.hi < 0.5 ? '↓有意' : '優位性なし';
    console.log(
      `${factor}: ${value} → 陽線率 ${fmtPct(w.p)} (n=${s.n}, 95%CI [${fmtPct(w.lo)}, ${fmtPct(w.hi)}]) ${sig}`
    );
  }

  if (estimates.length === 0) {
    console.log('\n判定可能な条件がありません。');
    process.exit(2);
  }

  const pooled = poolEstimates(estimates);
  const significant = estimates.filter((e) => e.lo > 0.5 || e.hi < 0.5);

  console.log('\n--- 総合 ---');
  if (pooled != null) {
    console.log(`統合推定(頻度の加重平均): 次足が上がる確率 ${fmtPct(pooled)} / 下がる確率 ${fmtPct(1 - pooled)}`);
  }
  if (significant.length === 0) {
    console.log('※ 現在の条件はいずれも95%信頼区間が50%を跨いでおり、統計的な優位性は確認できない。');
    console.log('  この状況でのエントリーは実質コイントスであり、見送りが統計的に正しい判断。');
  } else {
    console.log(`※ 統計的に有意な偏りがある条件: ${significant.map((e) => `${e.factor}=${e.value}`).join(', ')}`);
  }

  const breakEven = 1 / payout;
  console.log(`\nペイアウト${payout}倍の場合の損益分岐勝率: ${fmtPct(breakEven)}`);
  if (pooled != null) {
    const edge = Math.max(pooled, 1 - pooled);
    if (edge > breakEven && significant.length > 0) {
      console.log(`統合推定 ${fmtPct(edge)} は分岐点を上回るが、これは過去頻度であり将来を保証しない。`);
    } else {
      console.log(`統合推定 ${fmtPct(edge)} は分岐点 ${fmtPct(breakEven)} に届かない。期待値はマイナス。`);
    }
  }
}

main().catch((e) => { console.error(e.message); process.exit(1); });
