'use strict';

const { decide } = require('./strategy');
const {
  lotFromRisk,
  canOpenNew,
  effectiveRiskPct,
  dailyLossExceeded,
  liveGateReasons,
  forbidMartingale,
  pipValuePerLot
} = require('./risk');
const paper = require('./paper-broker');
const { writeSignals } = require('./adapters/signal-file');
const metaapi = require('./adapters/metaapi');
const { fetchYahooH1 } = require('./market-data');
const commanderMod = require('./commander');
const { loadConfig, todayUTC, roundTo, pipSize } = require('./util');

function loadAllConfig() {
  const strategy = loadConfig('strategy');
  const risk = loadConfig('risk');
  const runtime = loadConfig('runtime', { live_enabled: false, adapter: 'paper' });
  if (!strategy || !risk) throw new Error('config/strategy.json or config/risk.json missing');
  return { strategy, risk, runtime };
}

function lastClosedLot(book, symbol) {
  const closed = (book.closed || []).filter((c) => c.symbol === symbol);
  if (!closed.length) return { lot: null, pnl: null };
  const last = closed[closed.length - 1];
  return { lot: last.lot, pnl: last.pnl };
}

function applySpread(price, side, symbol, spreadPips) {
  const pip = pipSize(symbol);
  const half = (spreadPips * pip) / 2;
  return side === 'BUY' ? price + half : price - half;
}

async function fetchPrices(strategy, { fixtureBySymbol } = {}) {
  const prices = {};
  const barsBySymbol = {};
  const errors = {};
  for (const symbol of strategy.symbols) {
    try {
      const bars = fixtureBySymbol?.[symbol] || await fetchYahooH1(symbol);
      if (!bars.length) throw new Error('no bars');
      barsBySymbol[symbol] = bars;
      prices[symbol] = bars[bars.length - 1].close;
    } catch (err) {
      errors[symbol] = err.message;
    }
  }
  return { prices, barsBySymbol, errors };
}

function buildIntent({ symbol, decision, book, risk, commander, now, spreadPips }) {
  if (decision.action === 'CLOSE') {
    const pos = (book.positions || []).find((p) => p.symbol === symbol);
    if (!pos) return { symbol, action: 'FLAT', reason: 'close_but_flat' };
    return {
      symbol,
      action: 'CLOSE',
      reason: decision.reason,
      lot: pos.lot,
      side: pos.side
    };
  }

  if (decision.action !== 'BUY' && decision.action !== 'SELL') {
    return { symbol, action: decision.action, reason: decision.reason };
  }

  const gate = canOpenNew({ book, risk, commander, symbol });
  if (!gate.ok) return { symbol, action: 'FLAT', reason: gate.reason };

  const fill = applySpread(decision.close, decision.action, symbol, spreadPips);
  const sized = lotFromRisk({
    symbol,
    price: fill,
    slPrice: decision.sl,
    equity: book.equity,
    riskPct: effectiveRiskPct(risk, commander),
    maxLot: risk.max_lot,
    minLot: risk.min_lot,
    lotStep: risk.lot_step,
    contractSize: risk.contract_size
  });
  if (!sized.lot) return { symbol, action: 'FLAT', reason: sized.reason, detail: sized };

  const prev = lastClosedLot(book, symbol);
  if (forbidMartingale(prev.lot, sized.lot, prev.pnl)) {
    return { symbol, action: 'FLAT', reason: 'martingale_blocked', previousLot: prev.lot, nextLot: sized.lot };
  }

  return {
    symbol,
    action: decision.action,
    reason: decision.reason,
    lot: sized.lot,
    sl: roundTo(decision.sl, 5),
    tp: roundTo(decision.tp, 5),
    price: fill,
    pip_value: pipValuePerLot(symbol, fill, risk.contract_size),
    rsi: decision.rsi,
    atr: decision.atr,
    now
  };
}

function applyPaper(book, intent, now, prices, risk) {
  if (intent.action === 'CLOSE') {
    return paper.closePosition(book, intent.symbol, prices[intent.symbol], now, intent.reason);
  }
  if (intent.action === 'BUY' || intent.action === 'SELL') {
    const commission = (risk.commission_per_lot || 0) * intent.lot;
    return paper.openPosition(book, {
      symbol: intent.symbol,
      side: intent.action,
      lot: intent.lot,
      price: intent.price,
      sl: intent.sl,
      tp: intent.tp,
      pip_value: intent.pip_value,
      now,
      reason: intent.reason,
      commission
    });
  }
  return null;
}

async function maybeLive(runtime, commander, env, intent) {
  const reasons = liveGateReasons({ runtime, commander, env });
  if (reasons.length) return { sent: false, reasons };
  if (runtime.adapter !== 'metaapi') return { sent: false, reasons: ['adapter_not_metaapi'] };
  if (!['BUY', 'SELL', 'CLOSE'].includes(intent.action)) return { sent: false, reasons: ['not_an_order'] };
  const result = await metaapi.submitTrade(env, {
    ...intent,
    clientId: `xmge_${intent.symbol}_${Date.now()}`
  });
  return { sent: true, result };
}

async function runTick({ now = new Date(), env = process.env, dryRun = false, fixtureBySymbol = null } = {}) {
  const { strategy, risk, runtime } = loadAllConfig();
  let commander = commanderMod.loadCommander();

  if (!dryRun) {
    const synced = await commanderMod.syncFromGitHubIssue({
      token: env.GITHUB_TOKEN,
      repo: env.GITHUB_REPOSITORY,
      now
    });
    commander = synced.commander;
  }

  let book = paper.loadBook(risk);
  book = paper.rolloverDaily(book, now);

  const { prices, barsBySymbol, errors } = await fetchPrices(strategy, { fixtureBySymbol });
  paper.hitStops(book, prices, now);
  paper.markToMarket(book, prices);

  if (dailyLossExceeded(book, risk, todayUTC(now))) {
    commander = commanderMod.applyCommand(commander, {
      command: 'HALT',
      source: 'risk-guard',
      reason: 'max_daily_loss',
      now
    });
    if (!dryRun) commanderMod.saveCommander(commander);
    for (const p of [...book.positions]) {
      paper.closePosition(book, p.symbol, prices[p.symbol] ?? p.mark, now, 'daily_loss_halt');
    }
    paper.markToMarket(book, prices);
  }

  const intents = [];
  const liveResults = [];
  const halted = commander.command === 'HALT';

  for (const symbol of strategy.symbols) {
    const bars = barsBySymbol[symbol];
    if (!bars) {
      intents.push({ symbol, action: 'FLAT', reason: `data_error:${errors[symbol] || 'missing'}` });
      continue;
    }
    const position = (book.positions || []).find((p) => p.symbol === symbol) || null;
    const decision = halted
      ? (position ? { action: 'CLOSE', reason: 'halt' } : { action: 'FLAT', reason: 'halt' })
      : decide(bars, now, position, strategy);
    const intent = buildIntent({
      symbol,
      decision,
      book,
      risk,
      commander,
      now,
      spreadPips: risk.spread_pips
    });
    intents.push(intent);
    applyPaper(book, intent, now, prices, risk);
    paper.markToMarket(book, prices);

    if (!dryRun && runtime.adapter === 'metaapi') {
      liveResults.push(await maybeLive(runtime, commander, env, intent));
    }
  }

  const signals = dryRun ? { kind: 'shadow_signals', updated_at: now.toISOString(), intents } : writeSignals(intents, now);
  if (!dryRun) paper.saveBook(book);

  return {
    now: now.toISOString(),
    commander,
    runtime: { adapter: runtime.adapter, live_enabled: runtime.live_enabled },
    live_gate: liveGateReasons({ runtime, commander, env }),
    prices,
    data_errors: errors,
    intents,
    signals,
    book,
    liveResults,
    dryRun
  };
}

module.exports = {
  loadAllConfig,
  buildIntent,
  runTick
};

if (require.main === module) {
  const dryRun = process.argv.includes('--dry-run');
  runTick({ dryRun }).then((result) => {
    const summary = {
      now: result.now,
      commander: result.commander.command,
      live_gate: result.live_gate,
      data_errors: result.data_errors,
      intents: result.intents.map((i) => ({ symbol: i.symbol, action: i.action, reason: i.reason, lot: i.lot })),
      paper_equity: result.book.equity,
      dryRun: result.dryRun
    };
    console.log(JSON.stringify(summary, null, 2));
  }).catch((err) => {
    console.error(`tick failed: ${err.message}`);
    process.exit(1);
  });
}
