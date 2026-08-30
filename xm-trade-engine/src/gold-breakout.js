'use strict';

const path = require('path');
const { atrSeries } = require('./indicators');
const { todayUTC, roundTo, pipSize, readJSON, writeJSON, OUTPUT_DIR } = require('./util');

const GOLD_STATE_PATH = path.join(OUTPUT_DIR, 'state', 'gold.json');

/**
 * asia_* / london_* は GoldLondonBreakout と同じブローカーサーバー時刻。
 * Yahoo 足は UTC なので broker_utc_offset_hours で窓をずらす。XM 冬期は +2、夏期は +3。
 */
function brokerUtcOffsetHours(cfg) {
  const n = Number(cfg && cfg.broker_utc_offset_hours);
  return Number.isFinite(n) ? n : 2;
}

function hourField(cfg, name, legacy, fallback) {
  const n = Number(cfg && (cfg[name] ?? cfg[legacy]));
  return Number.isFinite(n) ? n : fallback;
}

function goldWindows(cfg) {
  return {
    offset: brokerUtcOffsetHours(cfg),
    asiaStart: hourField(cfg, 'asia_start_hour', 'asia_start_utc', 0),
    asiaEnd: hourField(cfg, 'asia_end_hour', 'asia_end_utc', 7),
    londonStart: hourField(cfg, 'london_start_hour', 'london_start_utc', 7),
    londonEnd: hourField(cfg, 'london_end_hour', 'london_end_utc', 11)
  };
}

function brokerDate(now, offsetHours) {
  return new Date(now.getTime() + offsetHours * 3600000);
}

function brokerParts(now, cfg) {
  const d = brokerDate(now, brokerUtcOffsetHours(cfg));
  return {
    y: d.getUTCFullYear(),
    m: d.getUTCMonth(),
    day: d.getUTCDate(),
    hour: d.getUTCHours(),
    dow: d.getUTCDay()
  };
}

function brokerHour(now, cfg) {
  return brokerParts(now, cfg).hour;
}

function brokerHourStart(now, hour, cfg) {
  const p = brokerParts(now, cfg);
  return Date.UTC(p.y, p.m, p.day, hour, 0, 0) - brokerUtcOffsetHours(cfg) * 3600000;
}

function isGoldSymbol(symbol) {
  const base = String(symbol || '').replace(/[^A-Z]/gi, '').toUpperCase();
  return base.includes('XAU') || base.includes('GOLD');
}

function isFirstFriday(date, cfg) {
  const offset = cfg == null ? 0 : brokerUtcOffsetHours(cfg);
  const d = brokerDate(date, offset);
  return d.getUTCDay() === 5 && d.getUTCDate() <= 7;
}

function barsInWindow(bars, startMs, endMs) {
  return (bars || []).filter((b) => b.time >= startMs && b.time < endMs);
}

function groupDaily(bars) {
  const map = new Map();
  for (const b of bars || []) {
    const d = new Date(b.time).toISOString().slice(0, 10);
    let g = map.get(d);
    if (!g) {
      map.set(d, {
        time: Date.parse(`${d}T00:00:00.000Z`),
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close
      });
    } else {
      g.high = Math.max(g.high, b.high);
      g.low = Math.min(g.low, b.low);
      g.close = b.close;
    }
  }
  return [...map.values()];
}

function lastAtr(bars, period) {
  const series = atrSeries(bars, period);
  for (let i = series.length - 1; i >= 0; i--) {
    if (series[i] != null) return series[i];
  }
  return null;
}

function asianRange(bars, now, cfg) {
  const w = goldWindows(cfg);
  const start = brokerHourStart(now, w.asiaStart, cfg);
  const end = brokerHourStart(now, w.asiaEnd, cfg);
  const window = barsInWindow(bars, start, end);
  if (!window.length) return null;
  return {
    high: Math.max(...window.map((b) => b.high)),
    low: Math.min(...window.map((b) => b.low)),
    close: window[window.length - 1].close,
    bars: window.length,
    start_ms: start,
    end_ms: end
  };
}

function emptyGoldState(now, reason) {
  return {
    kind: 'gold_semi_auto',
    disclaimer: 'Grok のエントリーは suggested_side に従うパネル操作。予想文は禁止。XM残高ではない。',
    date: todayUTC(now),
    status: 'idle',
    reason: reason || 'waiting_asia',
    arm: 'IDLE'
  };
}

/**
 * アジア終値がレンジのどこにいるかだけ見る。LLM の予想ではない。
 * 上1/3 → BUY、下1/3 → SELL、真ん中 → NONE（見送り）。
 */
function suggestedSide(asia) {
  if (!asia || !(asia.high > asia.low) || asia.close == null) return 'NONE';
  const pos = (asia.close - asia.low) / (asia.high - asia.low);
  if (pos >= 2 / 3) return 'BUY';
  if (pos <= 1 / 3) return 'SELL';
  return 'NONE';
}

/**
 * アジアレンジ確定後のセットアップ。Grok が ENTRY するまで発注しない。
 */
function proposeSetup({ bars, now, cfg, spreadPips = 0, dailyAtrOverride = null }) {
  if (!cfg || cfg.enabled === false) return emptyGoldState(now, 'disabled');
  const w = goldWindows(cfg);
  const parts = brokerParts(now, cfg);
  if (parts.dow === 0 || parts.dow === 6) return emptyGoldState(now, 'weekend');
  if (cfg.skip_first_friday && isFirstFriday(now, cfg)) return emptyGoldState(now, 'skip_first_friday');

  if (parts.hour < w.asiaEnd) return emptyGoldState(now, 'waiting_asia');

  const asia = asianRange(bars, now, cfg);
  if (!asia) return { ...emptyGoldState(now, 'no_asia_bars'), status: 'skipped' };

  const range = asia.high - asia.low;
  const dailyBars = groupDaily(bars);
  const dailyAtr = dailyAtrOverride ?? lastAtr(dailyBars, cfg.daily_atr_period);
  const h1Atr = lastAtr(bars, cfg.atr_period);
  if (!(dailyAtr > 0) || !(h1Atr > 0) || !(range > 0)) {
    return { ...emptyGoldState(now, 'atr_not_ready'), status: 'skipped', asia };
  }

  const frac = range / dailyAtr;
  if (frac < cfg.min_range_atr_frac) {
    return {
      ...emptyGoldState(now, 'range_too_small'),
      status: 'skipped',
      asia_high: asia.high,
      asia_low: asia.low,
      range: roundTo(range, 2),
      daily_atr: roundTo(dailyAtr, 2),
      range_atr_frac: roundTo(frac, 3)
    };
  }
  if (frac > cfg.max_range_atr_frac) {
    return {
      ...emptyGoldState(now, 'range_too_wide'),
      status: 'skipped',
      asia_high: asia.high,
      asia_low: asia.low,
      range: roundTo(range, 2),
      daily_atr: roundTo(dailyAtr, 2),
      range_atr_frac: roundTo(frac, 3)
    };
  }

  const pip = pipSize(cfg.symbol);
  if (spreadPips > cfg.max_spread_pips) {
    return { ...emptyGoldState(now, 'spread_too_wide'), status: 'skipped', spread_pips: spreadPips };
  }

  const buffer = h1Atr * cfg.breakout_buffer_atr;
  const slDist = h1Atr * cfg.sl_atr;
  const tpDist = slDist * cfg.reward_multiple;
  const side = suggestedSide(asia);

  return {
    kind: 'gold_semi_auto',
    disclaimer: 'Grok のエントリーは suggested_side に従うパネル操作。予想文は禁止。XM残高ではない。',
    date: todayUTC(now),
    status: 'awaiting_arm',
    reason: 'asia_locked',
    arm: 'IDLE',
    symbol: cfg.symbol,
    broker_hour: parts.hour,
    broker_utc_offset_hours: w.offset,
    asia_high: roundTo(asia.high, 2),
    asia_low: roundTo(asia.low, 2),
    asia_close: roundTo(asia.close, 2),
    range: roundTo(range, 2),
    daily_atr: roundTo(dailyAtr, 2),
    h1_atr: roundTo(h1Atr, 2),
    range_atr_frac: roundTo(frac, 3),
    suggested_side: side,
    buy_stop: roundTo(asia.high + buffer, 2),
    sell_stop: roundTo(asia.low - buffer, 2),
    sl_distance: roundTo(slDist, 2),
    tp_distance: roundTo(tpDist, 2),
    spread_pips: spreadPips,
    pip
  };
}

function applyArm(setup, { goldArm, goldArmDate, halted, now }) {
  if (!setup) return setup;
  const today = todayUTC(now);
  if (setup.date !== today) return setup;
  if (halted) {
    return { ...setup, status: setup.status === 'filled' ? setup.status : 'halted', arm: 'HALT', reason: 'halt' };
  }
  if (setup.status === 'skipped' || setup.status === 'filled' || setup.status === 'expired') return setup;
  if (goldArm === 'SKIP' && goldArmDate === today) {
    return { ...setup, status: 'skipped', arm: 'SKIP', reason: 'skip_command' };
  }
  if (goldArm === 'ARM' && goldArmDate === today && setup.status === 'awaiting_arm') {
    return { ...setup, status: 'armed', arm: 'ARM', entry_side: null, reason: 'armed_oco' };
  }
  if ((goldArm === 'BUY' || goldArm === 'SELL') && goldArmDate === today && setup.status === 'awaiting_arm') {
    return {
      ...setup,
      status: 'armed',
      arm: goldArm,
      entry_side: goldArm,
      reason: 'grok_entry'
    };
  }
  return setup;
}

function inLondonWindow(now, cfg) {
  const w = goldWindows(cfg);
  const hour = brokerHour(now, cfg);
  return hour >= w.londonStart && hour < w.londonEnd;
}

/**
 * ペーパー用。ARM 済みの OCO を、閉じた足の high/low で片方だけ約定させる。
 */
function detectFill(setup, bars, now, cfg) {
  const w = goldWindows(cfg);
  const hour = brokerHour(now, cfg);
  if (!setup || setup.status !== 'armed') {
    if (setup && setup.status === 'armed' && hour >= w.londonEnd) {
      return { ...setup, status: 'expired', reason: 'london_expired' };
    }
    return setup;
  }
  if (hour >= w.londonEnd) {
    return { ...setup, status: 'expired', reason: 'london_expired' };
  }
  if (!inLondonWindow(now, cfg)) return setup;
  const last = bars && bars[bars.length - 1];
  if (!last) return setup;
  const allowBuy = !setup.entry_side || setup.entry_side === 'BUY';
  const allowSell = !setup.entry_side || setup.entry_side === 'SELL';
  const hitBuy = allowBuy && last.high >= setup.buy_stop;
  const hitSell = allowSell && last.low <= setup.sell_stop;
  if (hitBuy && hitSell) {
    return { ...setup, status: 'armed', reason: 'ambiguous_both_sides' };
  }
  if (hitBuy) {
    return {
      ...setup,
      status: 'filled',
      fill_side: 'BUY',
      fill_price: setup.buy_stop,
      sl: roundTo(setup.buy_stop - setup.sl_distance, 2),
      tp: roundTo(setup.buy_stop + setup.tp_distance, 2),
      reason: 'oco_buy_stop'
    };
  }
  if (hitSell) {
    return {
      ...setup,
      status: 'filled',
      fill_side: 'SELL',
      fill_price: setup.sell_stop,
      sl: roundTo(setup.sell_stop + setup.sl_distance, 2),
      tp: roundTo(setup.sell_stop - setup.tp_distance, 2),
      reason: 'oco_sell_stop'
    };
  }
  return setup;
}

function loadGoldState() {
  return readJSON(GOLD_STATE_PATH, null);
}

function saveGoldState(state) {
  writeJSON(GOLD_STATE_PATH, state);
  return state;
}

module.exports = {
  GOLD_STATE_PATH,
  isGoldSymbol,
  isFirstFriday,
  asianRange,
  suggestedSide,
  groupDaily,
  proposeSetup,
  applyArm,
  detectFill,
  inLondonWindow,
  goldWindows,
  brokerUtcOffsetHours,
  brokerHour,
  brokerHourStart,
  loadGoldState,
  saveGoldState,
  emptyGoldState
};
