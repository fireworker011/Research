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
const gold = require('./gold-breakout');
const { loadConfig, todayUTC, roundTo, pipSize } = require('./util');

function loadAllConfig() {
  const strategy = loadConfig('strategy');
  const risk = loadConfig('risk');
  const runtime = loadConfig('runtime', { live_enabled: false, adapter: 'paper' });
  const goldCfg = loadConfig('gold', { enabled: false });
  if (!strategy || !risk) throw new Error('config/strategy.json or config/risk.json missing');
  return { strategy, risk, runtime, goldCfg };
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

async function runGoldPaper({ goldCfg, risk, book, commander, now, dryRun, fixtureBySymbol, errors, prices }) {
  const symbol = goldCfg.symbol || 'GOLD';
  let bars = fixtureBySymbol?.[symbol] || fixtureBySymbol?.XAUUSD || fixtureBySymbol?.GOLD;
  if (!bars) {
    try {
      bars = await fetchYahooH1('GOLD', { range: '60d' });
    } catch (err) {
      errors[symbol] = err.message;
      return { status: 'idle', reason: `data_error:${err.message}` };
    }
  }
  if (!bars.length) {
    errors[symbol] = 'no bars';
    return { status: 'idle', reason: 'no bars' };
  }
  prices[symbol] = bars[bars.length - 1].close;

  let setup = gold.proposeSetup({ bars, now, cfg: goldCfg, spreadPips: 0 });
  setup = gold.applyArm(setup, {
    goldArm: commander.gold_arm,
    goldArmDate: commander.gold_arm_date,
    halted: commander.command === 'HALT',
    now
  });
  setup = gold.autoArmIfDue(setup, goldCfg, now, commander.command === 'HALT');
  setup = gold.detectFill(setup, bars, now, goldCfg);

  const alreadyOpen = (book.positions || []).some((p) => p.symbol === symbol);
  const closedToday = (book.closed || []).some(
    (c) => c.symbol === symbol && (c.closed_at || '').slice(0, 10) === todayUTC(now)
  );

  if (setup.status === 'filled' && setup.fill_side && !alreadyOpen && !closedToday) {
    const sized = lotFromRisk({
      symbol,
      price: setup.fill_price,
      slPrice: setup.sl,
      equity: book.equity,
      riskPct: effectiveRiskPct(risk, commander),
      maxLot: risk.max_lot,
      minLot: risk.min_lot,
      lotStep: risk.lot_step,
      contractSize: goldCfg.contract_size
    });
    const prev = lastClosedLot(book, symbol);
    if (sized.lot && !forbidMartingale(prev.lot, sized.lot, prev.pnl)) {
      paper.openPosition(book, {
        symbol,
        side: setup.fill_side,
        lot: sized.lot,
        price: setup.fill_price,
        sl: setup.sl,
        tp: setup.tp,
        pip_value: pipValuePerLot(symbol, setup.fill_price, goldCfg.contract_size),
        now,
        reason: setup.reason,
        commission: (risk.commission_per_lot || 0) * sized.lot
      });
      setup = { ...setup, lot: sized.lot };
    } else {
      setup = { ...setup, lot: 0, lot_reason: sized.reason || 'martingale_blocked' };
    }
  }

  if (!dryRun) gold.saveGoldState(setup);
  if (!dryRun && setup.status === 'awaiting_arm') {
    await notifyGoldAwaitingArm(setup);
  }
  return setup;
}

async function notifyGoldAwaitingArm(setup) {
  const token = process.env.GITHUB_TOKEN || '';
  const repo = process.env.GITHUB_REPOSITORY || '';
  if (!token || !repo || !setup?.date) return;
  const marker = `gold-notice:${setup.date}`;
  const headers = {
    Authorization: `token ${token}`,
    Accept: 'application/vnd.github.v3+json',
    'content-type': 'application/json'
  };
  const base = `https://api.github.com/repos/${repo}`;
  const searchRes = await fetch(`${base}/issues?state=open&per_page=100`, { headers });
  const existing = await searchRes.json().catch(() => []);
  const found = Array.isArray(existing) ? existing.find((i) => i.title === commanderMod.ISSUE_TITLE) : null;
  if (!found) return;
  const commentsRes = await fetch(`${base}/issues/${found.number}/comments?per_page=100`, { headers });
  const comments = await commentsRes.json().catch(() => []);
  if (Array.isArray(comments) && comments.some((c) => String(c.body || '').includes(marker))) return;
  const body = [
    marker,
    '',
    `Gold ${setup.date} はアジア確定。完全自動なので ENTRY は出すな。このコメントは指令ではない。`,
    `asia ${setup.asia_low} – ${setup.asia_high} close ${setup.asia_close} frac ${setup.range_atr_frac}`,
    `BuyStop ${setup.buy_stop} / SellStop ${setup.sell_stop}`,
    `chart/paper suggested_side: ${setup.suggested_side}（参考。EA は OCO 両方）`,
    '',
    '止めるなら `KILL_SWITCH: HALT` または `SKIP: GOLD`。約定・決済告知は EA の xm-fill / xm-close。'
  ].join('\n');
  await fetch(`${base}/issues/${found.number}/comments`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ body })
  });
}

async function runTick({ now = new Date(), env = process.env, dryRun = false, fixtureBySymbol = null } = {}) {
  const { strategy, risk, runtime, goldCfg } = loadAllConfig();
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

  let goldState = null;
  if (goldCfg?.enabled) {
    goldState = await runGoldPaper({
      goldCfg,
      risk,
      book,
      commander,
      now,
      dryRun,
      fixtureBySymbol,
      errors,
      prices
    });
    paper.markToMarket(book, prices);
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
    gold: goldState,
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
      gold: result.gold ? { status: result.gold.status, reason: result.gold.reason, arm: result.gold.arm } : null,
      paper_equity: result.book.equity,
      dryRun: result.dryRun
    };
    console.log(JSON.stringify(summary, null, 2));
  }).catch((err) => {
    console.error(`tick failed: ${err.message}`);
    process.exit(1);
  });
}
