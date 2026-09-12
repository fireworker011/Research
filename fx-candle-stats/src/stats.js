'use strict';
// 統計コア: 条件付き頻度カウントのみで確率を出す。モデル推論・外挿は一切しない。
//
// 「次の5分足が上がる確率」を、過去データ中で現在と同じ条件だった場面の
// 実際の上昇頻度として算出する。各推定値には Wilson 95%信頼区間を付け、
// 区間が50%を跨ぐ場合は「統計的な優位性なし」と明示する。

const Z95 = 1.96;

function wilson(up, n, z = Z95) {
  if (n === 0) return { p: null, lo: null, hi: null };
  const p = up / n;
  const z2 = z * z;
  const denom = 1 + z2 / n;
  const center = (p + z2 / (2 * n)) / denom;
  const half = (z * Math.sqrt((p * (1 - p)) / n + z2 / (4 * n * n))) / denom;
  return { p, lo: Math.max(0, center - half), hi: Math.min(1, center + half) };
}

function direction(candle) {
  if (candle.c > candle.o) return 'U';
  if (candle.c < candle.o) return 'D';
  return 'F'; // 同値(doji)
}

function jstHour(unixSec) {
  return new Date((unixSec + 9 * 3600) * 1000).getUTCHours();
}

function session(unixSec) {
  const h = jstHour(unixSec);
  if (h >= 9 && h < 15) return '東京 (9-15時JST)';
  if (h >= 15 && h < 21) return '欧州 (15-21時JST)';
  if (h >= 21 || h < 2) return 'NY (21-2時JST)';
  return '閑散 (2-9時JST)';
}

function rsi14(closes) {
  // 各indexに対するRSI(14)。先頭14本はnull。
  const out = new Array(closes.length).fill(null);
  if (closes.length < 15) return out;
  let gain = 0, loss = 0;
  for (let i = 1; i <= 14; i++) {
    const d = closes[i] - closes[i - 1];
    if (d > 0) gain += d; else loss -= d;
  }
  let avgGain = gain / 14, avgLoss = loss / 14;
  out[14] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  for (let i = 15; i < closes.length; i++) {
    const d = closes[i] - closes[i - 1];
    avgGain = (avgGain * 13 + Math.max(d, 0)) / 14;
    avgLoss = (avgLoss * 13 + Math.max(-d, 0)) / 14;
    out[i] = avgLoss === 0 ? 100 : 100 - 100 / (1 + avgGain / avgLoss);
  }
  return out;
}

function rsiZone(v) {
  if (v == null) return null;
  if (v < 30) return 'RSI<30 (売られすぎ)';
  if (v < 45) return 'RSI 30-45';
  if (v < 55) return 'RSI 45-55 (中立)';
  if (v < 70) return 'RSI 55-70';
  return 'RSI>70 (買われすぎ)';
}

function bodyZone(candle, avgBody) {
  if (!avgBody) return null;
  const r = Math.abs(candle.c - candle.o) / avgBody;
  if (r < 0.5) return '実体小 (平均の0.5倍未満)';
  if (r < 1.5) return '実体中 (平均の0.5-1.5倍)';
  return '実体大 (平均の1.5倍超)';
}

function streakOf(dirs, i) {
  // index i で終わる連続同方向の本数(最大5+)
  const d = dirs[i];
  if (d === 'F') return null;
  let n = 1;
  while (i - n >= 0 && dirs[i - n] === d && n < 5) n++;
  const label = n >= 5 ? '5+' : String(n);
  return `${d === 'U' ? '陽線' : '陰線'}${label}連続`;
}

// candles[i] を「直近の確定足」として、candles[i+1] の方向を予測する際の条件を列挙
function extractConditions(candles, i, ctx) {
  const { dirs, rsis, avgBody } = ctx;
  const conds = {};
  if (dirs[i] !== 'F') conds['直前1本'] = dirs[i] === 'U' ? '陽線' : '陰線';
  if (i >= 1 && dirs[i] !== 'F' && dirs[i - 1] !== 'F') {
    conds['直前2本'] = [dirs[i - 1], dirs[i]].map((d) => (d === 'U' ? '陽' : '陰')).join('→');
  }
  if (i >= 2 && dirs[i] !== 'F' && dirs[i - 1] !== 'F' && dirs[i - 2] !== 'F') {
    conds['直前3本'] = [dirs[i - 2], dirs[i - 1], dirs[i]].map((d) => (d === 'U' ? '陽' : '陰')).join('→');
  }
  const nextOpenTime = candles[i].t + 300; // 予測対象足の開始時刻
  conds['時間帯(JST)'] = `${jstHour(nextOpenTime)}時台`;
  conds['セッション'] = session(nextOpenTime);
  const st = streakOf(dirs, i);
  if (st) conds['連続数'] = st;
  const rz = rsiZone(rsis[i]);
  if (rz) conds['RSI(14)'] = rz;
  const bz = bodyZone(candles[i], avgBody);
  if (bz) conds['直前足の実体'] = bz;
  return conds;
}

function buildContext(candles) {
  const dirs = candles.map(direction);
  const rsis = rsi14(candles.map((c) => c.c));
  const bodies = candles.map((c) => Math.abs(c.c - c.o));
  const avgBody = bodies.reduce((a, b) => a + b, 0) / (bodies.length || 1);
  return { dirs, rsis, avgBody };
}

// 全履歴を走査して、ファクター×条件値ごとの {up, n} テーブルを作る
function buildTables(candles) {
  const ctx = buildContext(candles);
  const tables = {}; // factor -> value -> {up, n}
  for (let i = 2; i < candles.length - 1; i++) {
    // 予測対象は i+1。ただし5分より大きいギャップ(週末・欠損)を跨ぐサンプルは除外
    if (candles[i + 1].t - candles[i].t !== 300) continue;
    const outcome = ctx.dirs[i + 1];
    if (outcome === 'F') continue;
    const up = outcome === 'U' ? 1 : 0;
    const conds = extractConditions(candles, i, ctx);
    for (const [factor, value] of Object.entries(conds)) {
      if (!tables[factor]) tables[factor] = {};
      if (!tables[factor][value]) tables[factor][value] = { up: 0, n: 0 };
      tables[factor][value].up += up;
      tables[factor][value].n += 1;
    }
  }
  return { tables, ctx };
}

// 各ファクターの推定値を逆分散重み付きの対数オッズ平均で統合する。
// これは頻度の加重平均であってモデルによる推論ではない。
function poolEstimates(estimates) {
  let num = 0, den = 0;
  for (const e of estimates) {
    if (e.n < 30 || e.p === 0 || e.p === 1) continue; // 小標本・退化は統合から除外
    const logit = Math.log(e.p / (1 - e.p));
    const w = e.n * e.p * (1 - e.p); // 逆分散重み
    num += w * logit;
    den += w;
  }
  if (den === 0) return null;
  const pooled = 1 / (1 + Math.exp(-num / den));
  return pooled;
}

module.exports = {
  wilson, direction, jstHour, session, rsi14, rsiZone, bodyZone,
  extractConditions, buildContext, buildTables, poolEstimates, Z95,
};
