'use strict';
// 過去60日の5分足全体を集計し、条件ごとの「次足が陽線だった頻度」を一覧表示する。
// 使い方: node src/analyze.js USDJPY [--min-n 50]

const { fetchCandles, saveCache, loadCache } = require('./fetch');
const { buildTables, wilson } = require('./stats');

function fmtPct(x) {
  return (x * 100).toFixed(1).padStart(5) + '%';
}

function significance(lo, hi, base) {
  let vs50;
  if (lo > 0.5) vs50 = '↑50%超え有意';
  else if (hi < 0.5) vs50 = '↓50%割れ有意';
  else vs50 = ' 優位性なし';
  // ベースレート(期間全体の地合い)を超える情報を持つかも併記する。
  // 上昇トレンド期はほぼ全条件が50%を超えて見えるが、それは地合いであって条件の予測力ではない。
  let vsBase;
  if (lo > base) vsBase = '+地合い超';
  else if (hi < base) vsBase = '-地合い割れ';
  else vsBase = ' 地合い並み';
  return `${vs50} / ${vsBase}`;
}

async function main() {
  const args = process.argv.slice(2);
  const pair = (args.find((a) => !a.startsWith('--')) || 'USDJPY').toUpperCase();
  const minN = parseInt((args.find((a) => a.startsWith('--min-n=')) || '--min-n=50').split('=')[1], 10);
  const useCache = args.includes('--cached');

  let data = useCache ? loadCache(pair) : null;
  if (!data) {
    console.log(`${pair} の5分足(直近60日)を取得中...`);
    data = await fetchCandles(pair);
    saveCache(data);
  }
  const candles = data.candles;
  const { tables } = buildTables(candles);

  const totalUp = candles.filter((c, i) => i > 0 && c.c > c.o).length;
  const totalDown = candles.filter((c, i) => i > 0 && c.c < c.o).length;
  const base = totalUp / (totalUp + totalDown);

  console.log('');
  console.log(`=== ${pair} 5分足 統計レポート (${candles.length}本 / 直近60日) ===`);
  console.log(`ベースレート(全期間の陽線率): ${fmtPct(base)}  ※これが比較の基準`);
  console.log('各行: 条件 | 次足の陽線率 | 標本数 | 95%信頼区間 | 判定');

  for (const [factor, values] of Object.entries(tables)) {
    console.log(`\n--- ${factor} ---`);
    const rows = Object.entries(values)
      .filter(([, s]) => s.n >= minN)
      .map(([value, s]) => ({ value, ...s, ...wilson(s.up, s.n) }))
      .sort((a, b) => b.p - a.p);
    for (const r of rows) {
      console.log(
        `${r.value.padEnd(22)} ${fmtPct(r.p)}  n=${String(r.n).padStart(5)}  ` +
        `[${fmtPct(r.lo)}, ${fmtPct(r.hi)}]  ${significance(r.lo, r.hi, base)}`
      );
    }
    if (rows.length === 0) console.log(`(標本数${minN}以上の条件なし)`);
  }

  console.log('\n読み方:');
  console.log('・「50%超え/割れ有意」= 95%信頼区間が50%を跨がない。バイナリーの賭けの向きとして意味がある偏り。');
  console.log(`・「地合い超/割れ」= 信頼区間がベースレート${fmtPct(base).trim()}も跨がない。期間全体のトレンドでは説明できない、条件固有の予測力がある。`);
  console.log('・地合い並みの条件は、単に期間のトレンドを反映しているだけの可能性が高い(トレンドが変われば消える)。');
}

main().catch((e) => { console.error(e.message); process.exit(1); });
