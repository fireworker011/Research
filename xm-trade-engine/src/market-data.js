'use strict';

const YAHOO_BASE = 'https://query1.finance.yahoo.com/v8/finance/chart';

const YAHOO_SYMBOLS = {
  EURUSD: 'EURUSD=X',
  GBPUSD: 'GBPUSD=X',
  USDJPY: 'USDJPY=X',
  GOLD: 'XAUUSD=X',
  XAUUSD: 'XAUUSD=X'
};

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

async function fetchYahooH1(symbol, { range = '60d', interval = '1h', timeoutMs = 15000 } = {}) {
  const yahoo = mapYahooSymbol(symbol);
  const url = `${YAHOO_BASE}/${encodeURIComponent(yahoo)}?interval=${encodeURIComponent(interval)}&range=${encodeURIComponent(range)}`;
  const ctrl = new AbortController();
  const t = setTimeout(() => ctrl.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: ctrl.signal,
      headers: {
        'User-Agent': 'xm-trade-engine/1.0 (paper research; not an official XM client)'
      }
    });
    if (!res.ok) throw new Error(`yahoo HTTP ${res.status}`);
    const payload = await res.json();
    if (payload?.chart?.error) throw new Error(`yahoo error ${payload.chart.error.description || ''}`);
    return parseYahooChart(payload);
  } finally {
    clearTimeout(t);
  }
}

module.exports = {
  YAHOO_SYMBOLS,
  mapYahooSymbol,
  dropIncompleteLastBar,
  parseYahooChart,
  fetchYahooH1
};
