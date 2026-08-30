'use strict';

function sma(values, period) {
  if (values.length < period) return null;
  let sum = 0;
  for (let i = values.length - period; i < values.length; i++) sum += values[i];
  return sum / period;
}

/** EMA. 最初の period 本は SMA でシードし、以降は k=2/(period+1)。 */
function emaSeries(closes, period) {
  const out = new Array(closes.length).fill(null);
  if (closes.length < period) return out;
  let seed = 0;
  for (let i = 0; i < period; i++) seed += closes[i];
  seed /= period;
  out[period - 1] = seed;
  const k = 2 / (period + 1);
  for (let i = period; i < closes.length; i++) {
    out[i] = closes[i] * k + out[i - 1] * (1 - k);
  }
  return out;
}

function lastDefined(series) {
  for (let i = series.length - 1; i >= 0; i--) {
    if (series[i] != null) return { index: i, value: series[i] };
  }
  return null;
}

/** Wilder ATR。true range の SMA シード → Wilder 平滑。 */
function atrSeries(bars, period) {
  const out = new Array(bars.length).fill(null);
  if (bars.length < period + 1) return out;
  const tr = new Array(bars.length).fill(null);
  tr[0] = bars[0].high - bars[0].low;
  for (let i = 1; i < bars.length; i++) {
    const prevClose = bars[i - 1].close;
    const highLow = bars[i].high - bars[i].low;
    const highClose = Math.abs(bars[i].high - prevClose);
    const lowClose = Math.abs(bars[i].low - prevClose);
    tr[i] = Math.max(highLow, highClose, lowClose);
  }
  let seed = 0;
  for (let i = 1; i <= period; i++) seed += tr[i];
  out[period] = seed / period;
  for (let i = period + 1; i < bars.length; i++) {
    out[i] = (out[i - 1] * (period - 1) + tr[i]) / period;
  }
  return out;
}

/** Wilder RSI。 */
function rsiSeries(closes, period) {
  const out = new Array(closes.length).fill(null);
  if (closes.length < period + 1) return out;
  const gains = [];
  const losses = [];
  for (let i = 1; i < closes.length; i++) {
    const diff = closes[i] - closes[i - 1];
    gains.push(Math.max(diff, 0));
    losses.push(Math.max(-diff, 0));
  }
  let avgGain = 0;
  let avgLoss = 0;
  for (let i = 0; i < period; i++) {
    avgGain += gains[i];
    avgLoss += losses[i];
  }
  avgGain /= period;
  avgLoss /= period;
  const rsiAt = (g, l) => {
    if (l === 0) return 100;
    if (g === 0) return 0;
    const rs = g / l;
    return 100 - 100 / (1 + rs);
  };
  out[period] = rsiAt(avgGain, avgLoss);
  for (let i = period; i < gains.length; i++) {
    avgGain = (avgGain * (period - 1) + gains[i]) / period;
    avgLoss = (avgLoss * (period - 1) + losses[i]) / period;
    out[i + 1] = rsiAt(avgGain, avgLoss);
  }
  return out;
}

function snapshot(bars, params) {
  const closes = bars.map((b) => b.close);
  const emaFast = emaSeries(closes, params.ema_fast);
  const emaSlow = emaSeries(closes, params.ema_slow);
  const rsi = rsiSeries(closes, params.rsi_period);
  const atr = atrSeries(bars, params.atr_period);
  const i = bars.length - 1;
  return {
    close: closes[i],
    prevClose: i > 0 ? closes[i - 1] : null,
    emaFast: emaFast[i],
    emaSlow: emaSlow[i],
    prevEmaFast: i > 0 ? emaFast[i - 1] : null,
    rsi: rsi[i],
    atr: atr[i]
  };
}

module.exports = {
  sma,
  emaSeries,
  atrSeries,
  rsiSeries,
  lastDefined,
  snapshot
};
