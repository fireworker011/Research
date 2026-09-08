'use strict';

const YAHOO_BASE = 'https://query1.finance.yahoo.com/v8/finance/chart';
const OKX_CANDLES = 'https://www.okx.com/api/v5/market/candles';
const TV_SCAN = 'https://scanner.tradingview.com';

const UA = 'xm-trade-engine/1.0 (paper research; not an official XM client)';

const YAHOO_SYMBOLS = {
  EURUSD: 'EURUSD=X',
  GBPUSD: 'GBPUSD=X',
  USDJPY: 'USDJPY=X',
  GOLD: 'XAUUSD=X',
  XAUUSD: 'XAUUSD=X'
};

const OKX_BAR = {
  '15m': '15m',
  '15M': '15m',
  '1h': '1H',
  '1H': '1H',
  '60m': '1H',
  '1d': '1D',
  '1D': '1D'
};

const TV_COLUMNS = [
  'close',
  'open',
  'high',
  'low',
  'change',
  'change_abs',
  'RSI',
  'ATR',
  'ATR|15',
  'ATR|60',
  'SMA20',
  'SMA50',
  'Recommend.All'
];

function mapYahooSymbol(symbol) {
  const key = String(symbol || '').replace(/[^A-Za-z]/g, '').toUpperCase();
  return YAHOO_SYMBOLS[key] || `${key}=X`;
}

function dropIncompleteLastBar(bars) {
  if (bars.length <= 1) return bars.slice();
  return bars.slice(0, -1);
}

function parseYahooChart(payload) {
  const result = payload?.chart?.result?.[0];
  if (!result) throw new Error('yahoo chart missing result');
  const timestamps = result.timestamp || [];
  const quote = result.indicators?.quote?.[0] || {};
  const bars = [];
  for (let i = 0; i < timestamps.length; i++) {
    const open = quote.open?.[i];
    const high = quote.high?.[i];
    const low = quote.low?.[i];
    const close = quote.close?.[i];
    if (![open, high, low, close].every((n) => Number.isFinite(n))) continue;
    bars.push({
      time: timestamps[i] * 1000,
      open,
      high,
      low,
      close,
      volume: quote.volume?.[i] || 0
    });
  }
  return dropIncompleteLastBar(bars);
}

async function fetchJson(url, { timeoutMs = 15000, method = 'GET', body = null, headers = {} } = {}) {
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      method,
      signal: ctrl.signal,
      headers: { 'User-Agent': UA, ...headers },
      body
    });
    if (!res.ok) throw new Error(`HTTP ${res.status} ${url}`);
    return await res.json();
  } finally {
    clearTimeout(t);
  }
}

async function fetchYahooH1(symbol, { range = '60d', interval = '1h', timeoutMs = 15000 } = {}) {
  const yahoo = mapYahooSymbol(symbol);
  const url = `${YAHOO_BASE}/${encodeURIComponent(yahoo)}?interval=${encodeURIComponent(interval)}&range=${encodeURIComponent(range)}`;
  const payload = await fetchJson(url, { timeoutMs });
  if (payload?.chart?.error) throw new Error(`yahoo error ${payload.chart.error.description || ''}`);
  return parseYahooChart(payload);
}

function parseOkxCandles(payload) {
  if (!payload || payload.code !== '0') {
    throw new Error(`okx candles ${payload?.code || 'empty'} ${payload?.msg || ''}`);
  }
  const rows = [...(payload.data || [])].reverse();
  const bars = [];
  for (const row of rows) {
    const time = Number(row[0]);
    const open = Number(row[1]);
    const high = Number(row[2]);
    const low = Number(row[3]);
    const close = Number(row[4]);
    if (![time, open, high, low, close].every((n) => Number.isFinite(n))) continue;
    bars.push({
      time,
      open,
      high,
      low,
      close,
      volume: Number(row[5] || 0)
    });
  }
  return bars;
}

async function fetchOkxCandles(instId, bar, { limit = 300, timeoutMs = 15000 } = {}) {
  const mapped = OKX_BAR[bar] || bar;
  const url = `${OKX_CANDLES}?instId=${encodeURIComponent(instId)}&bar=${encodeURIComponent(mapped)}&limit=${encodeURIComponent(String(limit))}`;
  const payload = await fetchJson(url, { timeoutMs });
  return parseOkxCandles(payload);
}

/**
 * XM の GOLD スポット足。Yahoo XAUUSD=X は 404 になるので使わない。
 * OKX XAUT-USDT はスポット金に近い連続足（XM 気配ではない）。
 */
async function fetchGoldBars({ interval = '15m', cfg = {}, limit = 300 } = {}) {
  const instId = cfg.okx_inst_id || 'XAUT-USDT';
  const bars = await fetchOkxCandles(instId, interval, { limit });
  if (!bars.length) throw new Error(`okx ${instId} ${interval} empty`);
  return bars;
}

function parseTradingViewScan(payload, columns) {
  const out = [];
  for (const row of payload?.data || []) {
    const item = { ticker: row.s };
    (columns || []).forEach((name, i) => {
      item[name] = row.d ? row.d[i] : null;
    });
    out.push(item);
  }
  return out;
}

async function fetchTradingViewScan(market, tickers, columns = TV_COLUMNS, timeoutMs = 15000) {
  const url = `${TV_SCAN}/${market}/scan`;
  const payload = await fetchJson(url, {
    timeoutMs,
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      symbols: { tickers },
      columns
    })
  });
  return parseTradingViewScan(payload, columns);
}

async function fetchTradingViewSnapshot({ timeoutMs = 15000 } = {}) {
  const goldTickers = ['OANDA:XAUUSD', 'FX_IDC:XAUUSD', 'TVC:GOLD'];
  const fxTickers = ['OANDA:EURUSD', 'OANDA:GBPUSD', 'OANDA:USDJPY'];
  const [cfd, forex] = await Promise.all([
    fetchTradingViewScan('cfd', goldTickers, TV_COLUMNS, timeoutMs),
    fetchTradingViewScan('forex', fxTickers, TV_COLUMNS, timeoutMs)
  ]);
  const byTicker = {};
  for (const row of [...cfd, ...forex]) byTicker[row.ticker] = row;
  return {
    source: 'tradingview_scanner',
    disclaimer: 'TradingView 公開スキャナ。XM 気配ではない。エントリー方向の予想ではない。',
    fetched_at: new Date().toISOString(),
    gold: byTicker['OANDA:XAUUSD'] || byTicker['FX_IDC:XAUUSD'] || byTicker['TVC:GOLD'] || null,
    EURUSD: byTicker['OANDA:EURUSD'] || null,
    GBPUSD: byTicker['OANDA:GBPUSD'] || null,
    USDJPY: byTicker['OANDA:USDJPY'] || null,
    raw: byTicker
  };
}

module.exports = {
  YAHOO_SYMBOLS,
  TV_COLUMNS,
  mapYahooSymbol,
  dropIncompleteLastBar,
  parseYahooChart,
  parseOkxCandles,
  parseTradingViewScan,
  fetchYahooH1,
  fetchOkxCandles,
  fetchGoldBars,
  fetchTradingViewSnapshot
};
