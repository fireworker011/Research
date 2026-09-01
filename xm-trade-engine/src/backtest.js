'use strict';

const { decide } = require('./strategy');
const { lotFromRisk, effectiveRiskPct, canOpenNew, forbidMartingale, pipValuePerLot } = require('./risk');
const paper = require('./paper-broker');
const { loadAllConfig } = require('./tick');
const { fetchYahooH1 } = require('./market-data');
const { roundTo, pipSize } = require('./util');

function applySpread(price, side, symbol, spreadPips) {
  const pip = pipSize(symbol);
  const half = (spreadPips * pip) / 2;
  return side === 'BUY' ? price + half : price - half;
}

function replay(bars, strategy, risk, commander, { startBalance, nowFn } = {}) {
  const book = paper.emptyBook({ paper_start_balance: startBalance ?? risk.paper_start_balance });
  const prices = {};
  const minBars = strategy.ema_slow + 5;
  for (let i = minBars; i <= bars.length; i++) {
    const window = bars.slice(0, i);
    const last = window[window.length - 1];
    const now = nowFn ? nowFn(last) : new Date(last.time);
    const symbol = strategy.symbols[0];
    prices[symbol] = last.close;
    paper.rolloverDaily(book, now);
    paper.hitStops(book, prices, now);
    paper.markToMarket(book, prices);
    const position = (book.positions || []).find((p) => p.symbol === symbol) || null;
    const decision = decide(window, now, position, strategy);
    if (decision.action === 'CLOSE' && position) {
      paper.closePosition(book, symbol, last.close, now, decision.reason);
      paper.markToMarket(book, prices);
      continue;
    }
    if (decision.action !== 'BUY' && decision.action !== 'SELL') continue;
    const gate = canOpenNew({ book, risk, commander, symbol });
    if (!gate.ok) continue;
    const fill = applySpread(decision.close, decision.action, symbol, risk.spread_pips);
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
    if (!sized.lot) continue;
    const prev = (book.closed || []).filter((c) => c.symbol === symbol).slice(-1)[0];
    if (prev && forbidMartingale(prev.lot, sized.lot, prev.pnl)) continue;
    paper.openPosition(book, {
      symbol,
      side: decision.action,
      lot: sized.lot,
      price: fill,
      sl: decision.sl,
      tp: decision.tp,
      pip_value: pipValuePerLot(symbol, fill, risk.contract_size),
      now,
      reason: decision.reason,
      commission: (risk.commission_per_lot || 0) * sized.lot
    });
    paper.markToMarket(book, prices);
  }
  if (book.positions.length) {
    const last = bars[bars.length - 1];
    for (const p of [...book.positions]) {
      paper.closePosition(book, p.symbol, last.close, new Date(last.time), 'backtest_eod');
    }
    paper.markToMarket(book, { [strategy.symbols[0]]: last.close });
  }
  const pnls = book.closed.map((c) => c.pnl);
  const wins = pnls.filter((x) => x > 0).length;
  return {
    trades: book.closed.length,
    wins,
    losses: pnls.filter((x) => x < 0).length,
    win_rate: book.closed.length ? wins / book.closed.length : 0,
    net_pnl: roundTo(pnls.reduce((a, b) => a + b, 0), 2),
    end_equity: book.equity,
    closed: book.closed
  };
}

async function runBacktest({ yahoo = false, fixtureBars = null } = {}) {
  const { strategy, risk } = loadAllConfig();
  const commander = { command: 'PAPER_ONLY', risk_multiplier: 1 };
  const symbol = strategy.symbols[0];
  let bars = fixtureBars;
  let source = 'fixture';
  if (!bars && yahoo) {
    bars = await fetchYahooH1(symbol, { range: '1y' });
    source = 'yahoo';
  }
  if (!bars) throw new Error('no bars: pass fixture or --yahoo');
  const single = { ...strategy, symbols: [symbol] };
  const stats = replay(bars, single, risk, commander);
  return { source, symbol, bars: bars.length, ...stats };
}

module.exports = { replay, runBacktest };

if (require.main === module) {
  const yahoo = process.argv.includes('--yahoo');
  runBacktest({ yahoo }).then((s) => {
    console.log(JSON.stringify({
      note: '過去サンプルまたは合成データ。将来の期待値ではない。',
      source: s.source,
      symbol: s.symbol,
      bars: s.bars,
      trades: s.trades,
      wins: s.wins,
      losses: s.losses,
      win_rate: s.win_rate,
      net_pnl: s.net_pnl,
      end_equity: s.end_equity
    }, null, 2));
  }).catch((err) => {
    console.error(`backtest failed: ${err.message}`);
    process.exit(1);
  });
}
