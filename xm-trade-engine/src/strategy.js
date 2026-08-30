'use strict';

const { utcDay, utcHour } = require('./util');
const { snapshot } = require('./indicators');

const ACTIONS = Object.freeze(['FLAT', 'BUY', 'SELL', 'HOLD', 'CLOSE']);

function inSession(date, session) {
  const day = utcDay(date);
  if (day === 0 || day === 6) return false;
  const hour = utcHour(date);
  return hour >= session.utc_start_hour && hour < session.utc_end_hour;
}

function shouldFlattenFriday(date, session) {
  return utcDay(date) === 5 && utcHour(date) >= session.friday_flatten_utc_hour;
}

function trendOf(snap) {
  if (snap.emaFast == null || snap.emaSlow == null) return 'none';
  if (snap.emaFast > snap.emaSlow) return 'bull';
  if (snap.emaFast < snap.emaSlow) return 'bear';
  return 'none';
}

function crossedUp(snap) {
  return snap.prevClose != null && snap.prevEmaFast != null
    && snap.prevClose <= snap.prevEmaFast
    && snap.close > snap.emaFast;
}

function crossedDown(snap) {
  return snap.prevClose != null && snap.prevEmaFast != null
    && snap.prevClose >= snap.prevEmaFast
    && snap.close < snap.emaFast;
}

function atrOk(snap, close, filter) {
  if (!filter || snap.atr == null || close <= 0) return true;
  const ratio = snap.atr / close;
  if (ratio < filter.min_atr_over_close) return false;
  if (ratio > filter.max_atr_over_close) return false;
  return true;
}

/**
 * 閉じた足だけを見てエントリーを決める。LLM は呼ばない。
 * position は { side: 'BUY'|'SELL' } または null。
 */
function decide(bars, now, position, strategy) {
  if (!bars || bars.length < strategy.ema_slow + 5) {
    return { action: 'FLAT', reason: 'not_enough_bars' };
  }

  if (shouldFlattenFriday(now, strategy.session)) {
    if (position) return { action: 'CLOSE', reason: 'friday_flatten' };
    return { action: 'FLAT', reason: 'friday_flatten' };
  }

  if (!inSession(now, strategy.session)) {
    if (position) return { action: 'HOLD', reason: 'out_of_session_hold' };
    return { action: 'FLAT', reason: 'out_of_session' };
  }

  const snap = snapshot(bars, strategy);
  if (snap.emaFast == null || snap.emaSlow == null || snap.rsi == null || snap.atr == null) {
    return { action: 'FLAT', reason: 'indicators_not_ready' };
  }

  const trend = trendOf(snap);
  const slDist = snap.atr * strategy.sl_atr;
  const tpDist = snap.atr * strategy.tp_atr;

  if (position) {
    if (position.side === 'BUY' && trend !== 'bull') {
      return { action: 'CLOSE', reason: 'trend_flip', ...snap, trend };
    }
    if (position.side === 'SELL' && trend !== 'bear') {
      return { action: 'CLOSE', reason: 'trend_flip', ...snap, trend };
    }
    return { action: 'HOLD', reason: 'trend_intact', ...snap, trend };
  }

  if (!atrOk(snap, snap.close, strategy.atr_filter)) {
    return { action: 'FLAT', reason: 'atr_filter', ...snap, trend };
  }

  if (trend === 'bull' && crossedUp(snap) && snap.rsi < strategy.rsi_overbought) {
    return {
      action: 'BUY',
      reason: 'ema_cross_up_trend',
      sl: snap.close - slDist,
      tp: snap.close + tpDist,
      ...snap,
      trend
    };
  }

  if (trend === 'bear' && crossedDown(snap) && snap.rsi > strategy.rsi_oversold) {
    return {
      action: 'SELL',
      reason: 'ema_cross_down_trend',
      sl: snap.close + slDist,
      tp: snap.close - tpDist,
      ...snap,
      trend
    };
  }

  return { action: 'FLAT', reason: 'no_setup', ...snap, trend };
}

function validateStrategy(strategy) {
  const missing = [
    'ema_fast',
    'ema_slow',
    'rsi_period',
    'atr_period',
    'sl_atr',
    'tp_atr',
    'rsi_overbought',
    'rsi_oversold'
  ].filter((k) => strategy[k] == null);
  if (missing.length) throw new Error(`strategy missing: ${missing.join(',')}`);
  if (strategy.ema_fast >= strategy.ema_slow) throw new Error('ema_fast must be < ema_slow');
  if (strategy.sl_atr <= 0 || strategy.tp_atr <= 0) throw new Error('atr multiples must be > 0');
  if (strategy.rsi_oversold >= strategy.rsi_overbought) throw new Error('rsi bounds inverted');
}

module.exports = {
  ACTIONS,
  inSession,
  shouldFlattenFriday,
  decide,
  validateStrategy,
  trendOf
};
