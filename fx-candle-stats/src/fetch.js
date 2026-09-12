'use strict';
// Yahoo Finance chart API から5分足OHLCを取得する。APIキー不要。
// 5分足はYahoo側の制約で最大60日分。

const fs = require('fs');
const path = require('path');

const DATA_DIR = path.join(__dirname, '..', 'data');

function toYahooSymbol(pair) {
  // "USDJPY" -> "USDJPY=X"
  const p = pair.toUpperCase().replace(/[^A-Z]/g, '');
  if (!/^[A-Z]{6}$/.test(p)) {
    throw new Error(`通貨ペアは "USDJPY" のような6文字で指定してください: ${pair}`);
  }
  return `${p}=X`;
}

async function fetchCandles(pair, { range = '60d', interval = '5m' } = {}) {
  const symbol = toYahooSymbol(pair);
  const url = `https://query1.finance.yahoo.com/v8/finance/chart/${encodeURIComponent(symbol)}?interval=${interval}&range=${range}`;
  const res = await fetch(url, { headers: { 'User-Agent': 'Mozilla/5.0' } });
  if (!res.ok) throw new Error(`Yahoo Finance API error: HTTP ${res.status}`);
  const json = await res.json();
  const result = json.chart && json.chart.result && json.chart.result[0];
  if (!result) {
    throw new Error(`データ取得失敗: ${JSON.stringify(json.chart && json.chart.error)}`);
  }
  const ts = result.timestamp || [];
  const q = result.indicators.quote[0];
  const candles = [];
  for (let i = 0; i < ts.length; i++) {
    const o = q.open[i], h = q.high[i], l = q.low[i], c = q.close[i];
    if (o == null || h == null || l == null || c == null) continue;
    candles.push({ t: ts[i], o, h, l, c });
  }
  return {
    pair: pair.toUpperCase(),
    symbol,
    interval,
    fetchedAt: Math.floor(Date.now() / 1000),
    marketTime: result.meta.regularMarketTime,
    marketPrice: result.meta.regularMarketPrice,
    candles,
  };
}

function cachePath(pair) {
  return path.join(DATA_DIR, `${pair.toUpperCase()}_5m.json`);
}

function saveCache(data) {
  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.writeFileSync(cachePath(data.pair), JSON.stringify(data));
}

function loadCache(pair) {
  const p = cachePath(pair);
  if (!fs.existsSync(p)) return null;
  return JSON.parse(fs.readFileSync(p, 'utf8'));
}

module.exports = { fetchCandles, saveCache, loadCache, toYahooSymbol };

if (require.main === module) {
  const pair = process.argv[2] || 'USDJPY';
  fetchCandles(pair)
    .then((data) => {
      saveCache(data);
      const first = new Date(data.candles[0].t * 1000).toISOString();
      const last = new Date(data.candles[data.candles.length - 1].t * 1000).toISOString();
      console.log(`${data.pair}: ${data.candles.length}本の5分足を取得 (${first} 〜 ${last})`);
      console.log(`キャッシュ保存先: ${cachePath(pair)}`);
    })
    .catch((e) => { console.error(e.message); process.exit(1); });
}
