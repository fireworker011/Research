'use strict';

const { clamp, pipSize, roundTo } = require('./util');

const LIVE_CONFIRM_PHRASE = 'I_UNDERSTAND_THE_RISK';
const COMMANDS = Object.freeze(['HALT', 'PAPER_ONLY', 'RESUME', 'REDUCE_RISK']);

function riskMultiplier(commander) {
  const cmd = commander?.command || 'PAPER_ONLY';
  if (cmd === 'HALT') return 0;
  if (cmd === 'REDUCE_RISK') return 0.5 * (commander.risk_multiplier || 1);
  return commander?.risk_multiplier ?? 1;
}

function pipValuePerLot(symbol, price, contractSize = 100000) {
  const pip = pipSize(symbol);
  const base = String(symbol || '').replace(/[^A-Z]/gi, '').toUpperCase();
  if (base.endsWith('JPY')) {
    if (!price) return 0;
    return (pip / price) * contractSize;
  }
  return pip * contractSize;
}

function lotFromRisk({ symbol, price, slPrice, equity, riskPct, maxLot, minLot, lotStep, contractSize }) {
  const pip = pipSize(symbol);
  const slDist = Math.abs(price - slPrice);
  const slPips = slDist / pip;
  if (!(slPips > 0) || !(equity > 0) || !(riskPct > 0)) return { lot: 0, reason: 'invalid_inputs' };
  const pv = pipValuePerLot(symbol, price, contractSize);
  if (!(pv > 0)) return { lot: 0, reason: 'pip_value_zero' };
  const riskAmount = equity * (riskPct / 100);
  let lot = riskAmount / (slPips * pv);
  lot = Math.floor(lot / lotStep) * lotStep;
  lot = roundTo(lot, 2);
  if (lot < minLot) return { lot: 0, reason: 'lot_too_small', slPips, riskAmount };
  lot = clamp(lot, minLot, maxLot);
  return { lot, slPips, riskAmount, pipValue: pv };
}

function dailyLossExceeded(book, risk, nowDate) {
  const start = book.daily?.start_equity;
  if (!(start > 0)) return false;
  if (book.daily?.date !== nowDate) return false;
  const equity = book.equity ?? book.balance;
  const lossPct = ((start - equity) / start) * 100;
  return lossPct >= risk.max_daily_loss_pct;
}

function liveGateReasons({ runtime, commander, env }) {
  const reasons = [];
  if (!runtime?.live_enabled) reasons.push('runtime.live_enabled is false');
  const cmd = commander?.command || 'PAPER_ONLY';
  if (cmd === 'HALT') reasons.push('commander HALT');
  if (cmd === 'PAPER_ONLY') reasons.push('commander PAPER_ONLY');
  if ((env?.XM_LIVE_CONFIRM || '') !== LIVE_CONFIRM_PHRASE) {
    reasons.push(`XM_LIVE_CONFIRM is not ${LIVE_CONFIRM_PHRASE}`);
  }
  if (runtime?.adapter === 'metaapi') {
    if (!env?.METAAPI_TOKEN) reasons.push('METAAPI_TOKEN missing');
    if (!env?.METAAPI_ACCOUNT_ID) reasons.push('METAAPI_ACCOUNT_ID missing');
  }
  return reasons;
}

function canSendLiveOrder(ctx) {
  return liveGateReasons(ctx).length === 0;
}

function canOpenNew({ book, risk, commander, symbol }) {
  const cmd = commander?.command || 'PAPER_ONLY';
  if (cmd === 'HALT') return { ok: false, reason: 'halt' };
  if (riskMultiplier(commander) <= 0) return { ok: false, reason: 'risk_zero' };
  const open = book.positions || [];
  if (open.length >= risk.max_open_positions) return { ok: false, reason: 'max_open_positions' };
  if (open.some((p) => p.symbol === symbol)) return { ok: false, reason: 'already_in_symbol' };
  return { ok: true };
}

function effectiveRiskPct(risk, commander) {
  return risk.risk_per_trade_pct * riskMultiplier(commander);
}

function forbidMartingale(previousLot, nextLot, lastClosedPnl) {
  if (lastClosedPnl == null || lastClosedPnl >= 0) return false;
  return nextLot > previousLot;
}

module.exports = {
  LIVE_CONFIRM_PHRASE,
  COMMANDS,
  riskMultiplier,
  pipValuePerLot,
  lotFromRisk,
  dailyLossExceeded,
  liveGateReasons,
  canSendLiveOrder,
  canOpenNew,
  effectiveRiskPct,
  forbidMartingale
};
